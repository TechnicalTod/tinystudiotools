/**
 * TinyStudio AE Workfile Publisher (native ExtendScript).
 *
 * Layout mirrors Asset Manager / Maya workfile publisher:
 *   header (show / host / user / drive)
 *   left tree (shot → task) + right panel (workfile table, actions)
 *   variant field + Refresh / Open Selected / Publish
 *
 * No Python subprocess or external UI.
 */

var _publisherWindow = null;

var SHOT_TASKS = ["layout", "anim", "light", "techviz"];

function tinystudioRun() {
  try {
    if (_publisherWindow !== null) {
      try {
        _publisherWindow.close();
      } catch (closeErr) {
        /* ignore */
      }
      _publisherWindow = null;
    }
    _publisherWindow = buildPublisherWindow();
    _publisherWindow.onClose = function () {
      _publisherWindow = null;
    };
    _publisherWindow.center();
    _publisherWindow.show();
  } catch (err) {
    alert("Workfile Publisher failed:\n" + err.toString());
  }
}

// ---------------------------------------------------------------------------
// Context / path helpers

function slash(value) {
  /* ExtendScript can choke on regex literals like /\\/g — use RegExp or split/join */
  var s = String(value || "");
  var parts = s.split("\\");
  return parts.join("/");
}

function normalizeBaseShowDir(baseShow, showName) {
  var b = slash(baseShow || "S:/");
  var s = slash(showName);
  while (b.length > 0 && b.charAt(b.length - 1) === "/") {
    b = b.substring(0, b.length - 1);
  }
  if (s.length && b.length >= s.length) {
    var tail = b.substring(b.length - s.length);
    if (tail === s) {
      b = b.substring(0, b.length - s.length);
      while (b.length > 0 && b.charAt(b.length - 1) === "/") {
        b = b.substring(0, b.length - 1);
      }
    }
  }
  if (!b.length) {
    b = "S:";
  }
  return b + "/";
}

function resolveStudioContext() {
  var show = $.getenv("SHOW_NAME");
  if (!show || !String(show).length) {
    throw new Error(
      "SHOW_NAME is not set.\n\nLaunch After Effects through TinyStudioLauncher."
    );
  }
  show = String(show);
  var base = normalizeBaseShowDir($.getenv("TINYSTUDIO_BASE_SHOW_DIR"), show);
  var showRoot = base + show;
  return {
    show: show,
    baseShowDir: base,
    showRoot: showRoot,
    username: $.getenv("USERNAME") || "artist"
  };
}

function cleanVariant(value) {
  var text = String(value || "main")
    .replace(/^\s+/, "")
    .replace(/\s+$/, "")
    .toLowerCase()
    .replace(/\s+/g, "_");
  if (!/^[a-z0-9][a-z0-9_-]*$/.test(text)) {
    throw new Error(
      "Variant must start with a letter or number and use only lowercase letters, numbers, underscore, or dash."
    );
  }
  return text;
}

function padVersion(value) {
  var text = String(value);
  while (text.length < 3) {
    text = "0" + text;
  }
  return text;
}

function regexEscape(text) {
  return String(text).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function listSubdirs(folder) {
  var names = [];
  if (!folder || !folder.exists) {
    return names;
  }
  var entries = folder.getFiles();
  if (!entries) {
    return names;
  }
  if (!(entries instanceof Array)) {
    entries = [entries];
  }
  for (var i = 0; i < entries.length; i++) {
    var entry = entries[i];
    if (entry instanceof Folder && entry.name.charAt(0) !== ".") {
      names.push(entry.name);
    }
  }
  names.sort();
  return names;
}

function formatModified(file) {
  try {
    var d = file.modified;
    if (d && d instanceof Date) {
      function two(n) {
        return n < 10 ? "0" + n : String(n);
      }
      return (
        d.getFullYear() +
        "-" +
        two(d.getMonth() + 1) +
        "-" +
        two(d.getDate()) +
        " " +
        two(d.getHours()) +
        ":" +
        two(d.getMinutes())
      );
    }
    return String(d);
  } catch (e) {
    return "";
  }
}

function parseWorkfileEntry(file, shot, task) {
  var name = file.name;
  if (!/\.aep$/i.test(name)) {
    return null;
  }

  var versionMatch = /_v(\d+)\.aep$/i.exec(name);
  if (!versionMatch) {
    return null;
  }
  var version = parseInt(versionMatch[1], 10);

  var variant = "main";
  var strictRe = new RegExp(
    "^" +
      regexEscape(shot) +
      "_" +
      regexEscape(task) +
      "_([a-z0-9][a-z0-9_-]*)_v\\d+\\.aep$",
    "i"
  );
  var looseRe = new RegExp(
    "_" + regexEscape(task) + "_([a-z0-9][a-z0-9_-]*)_v\\d+\\.aep$",
    "i"
  );
  var anyVariantRe = /_([a-z0-9][a-z0-9_-]*)_v\d+\.aep$/i;

  var m = strictRe.exec(name);
  if (!m) {
    m = looseRe.exec(name);
  }
  if (!m) {
    m = anyVariantRe.exec(name);
  }
  if (m) {
    variant = String(m[1]).toLowerCase();
  }

  return {
    path: file,
    filename: name,
    variant: variant,
    version: version,
    modified: formatModified(file)
  };
}

function scanAllWorkfiles(folder, shot, task) {
  var results = [];
  if (!folder || !folder.exists) {
    return results;
  }
  var files = folder.getFiles("*.aep");
  if (!files) {
    return results;
  }
  if (!(files instanceof Array)) {
    files = [files];
  }
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    if (!(f instanceof File)) {
      continue;
    }
    var entry = parseWorkfileEntry(f, shot, task);
    if (!entry) {
      continue;
    }
    results.push(entry);
  }
  results.sort(function (a, b) {
    if (a.variant !== b.variant) {
      return a.variant < b.variant ? -1 : 1;
    }
    if (a.version !== b.version) {
      return b.version - a.version;
    }
    return a.filename < b.filename ? -1 : 1;
  });
  return results;
}

function nextVersionForVariant(folder, shot, task, variant) {
  var highest = 0;
  var files = scanAllWorkfiles(folder, shot, task);
  for (var i = 0; i < files.length; i++) {
    if (files[i].variant === variant && files[i].version > highest) {
      highest = files[i].version;
    }
  }
  return highest + 1;
}

function shotWorkFolder(ctx, episode, sequence, shot, task) {
  return new Folder(
    ctx.showRoot +
      "/episodes/" +
      episode +
      "/" +
      sequence +
      "/" +
      shot +
      "/work/ae/" +
      task
  );
}

function buildShotFile(ctx, episode, sequence, shot, task, variant, version) {
  var folder = shotWorkFolder(ctx, episode, sequence, shot, task);
  var name =
    shot + "_" + task + "_" + variant + "_v" + padVersion(version) + ".aep";
  return new File(folder.fsName + "/" + name);
}

function ensureFolder(folder) {
  if (!folder) {
    return false;
  }
  if (folder.exists) {
    return true;
  }
  var parent = folder.parent;
  if (parent && !parent.exists && !ensureFolder(parent)) {
    return false;
  }
  return folder.create();
}

function taskTreeLabel(task, folder, shot) {
  var count = scanAllWorkfiles(folder, shot, task).length;
  return count > 0 ? task + "  (" + count + ")" : task;
}

function parseTaskLabel(text) {
  return String(text || "")
    .replace(/\s+\(\d+\)\s*$/, "")
    .replace(/^\s+/, "")
    .replace(/\s+$/, "");
}

function taskSelectId(episode, sequence, shot, task) {
  return episode + "|" + sequence + "|" + shot + "|" + task;
}

function resolveTaskContext(win, node) {
  if (!node) {
    return null;
  }

  var selectId = node._selectId;
  if (!selectId) {
    try {
      selectId = node.helpTip;
    } catch (helpErr) {
      selectId = null;
    }
  }
  if (selectId && win._ctxById && win._ctxById[selectId]) {
    return win._ctxById[selectId];
  }
  if (node._ctx && node._ctx.kind === "task") {
    return node._ctx;
  }

  var nodeText = String(node.text || "");
  var registry = win._taskNodeRegistry;
  if (registry) {
    for (var i = 0; i < registry.length; i++) {
      if (registry[i].node === node) {
        return registry[i].ctx;
      }
      if (registry[i].id && registry[i].id === selectId) {
        return registry[i].ctx;
      }
      if (String(registry[i].node.text) === nodeText) {
        return registry[i].ctx;
      }
    }
  }

  return null;
}

function applyTreeSelection(win) {
  var ctx = resolveTaskContext(win, win.tree.selection);
  if (ctx && ctx.kind === "task") {
    win._selection = ctx;
    win._activeSelectId = taskSelectId(
      ctx.episode,
      ctx.sequence,
      ctx.shot,
      ctx.task
    );
  } else {
    win._selection = null;
    win._activeSelectId = null;
  }
  win.refreshTable();
  if (win.layout) {
    win.layout.layout(true);
  }
}

function clearTree(tree) {
  if (!tree || !tree.items) {
    return;
  }
  while (tree.items.length > 0) {
    tree.remove(tree.items[0]);
  }
}

function treeSelectionPath(ctx) {
  if (!ctx || ctx.kind !== "task") {
    return null;
  }
  return (
    "shot/" +
    ctx.episode +
    "/" +
    ctx.sequence +
    "/" +
    ctx.shot +
    "/" +
    ctx.task
  );
}

/**
 * ScriptUI TreeView expects labeled nodes via add("node", text).
 * Using add("node") then assigning .text often breaks hierarchy on AE hosts.
 */
function addFolderNode(parent, label, kind) {
  var node = parent.add("node", label);
  node._ctx = { kind: kind };
  return node;
}

function findChildByText(parent, text) {
  if (!parent || !parent.items) {
    return null;
  }
  for (var i = 0; i < parent.items.length; i++) {
    if (String(parent.items[i].text) === text) {
      return parent.items[i];
    }
  }
  return null;
}

function findShotNode(parent, shot) {
  if (!parent || !parent.items) {
    return null;
  }
  for (var i = 0; i < parent.items.length; i++) {
    var node = parent.items[i];
    if (node._ctx && node._ctx.kind === "shot" && node._ctx.shot === shot) {
      return node;
    }
  }
  return null;
}

function findTaskNode(parent, task) {
  if (!parent || !parent.items) {
    return null;
  }
  for (var i = 0; i < parent.items.length; i++) {
    var node = parent.items[i];
    if (node._ctx && node._ctx.kind === "task" && node._ctx.task === task) {
      return node;
    }
  }
  return null;
}

function populateWorkfileTree(win) {
  clearTree(win.tree);
  win._selection = null;
  win._taskNodeRegistry = [];
  win._ctxById = {};

  var episodesRoot = addFolderNode(win.tree, "episodes", "episodes_root");
  var episodes = listSubdirs(new Folder(win.ctx.showRoot + "/episodes"));
  for (var e = 0; e < episodes.length; e++) {
    var episode = episodes[e];
    var episodeNode = addFolderNode(episodesRoot, episode, "episode");
    var seqFolder = new Folder(win.ctx.showRoot + "/episodes/" + episode);
    var sequences = listSubdirs(seqFolder);
    for (var s = 0; s < sequences.length; s++) {
      var sequence = sequences[s];
      var sequenceNode = addFolderNode(episodeNode, sequence, "sequence");
      var shotFolder = new Folder(seqFolder.fsName + "/" + sequence);
      var shots = listSubdirs(shotFolder);
      for (var h = 0; h < shots.length; h++) {
        var shot = shots[h];
        var shotNode = sequenceNode.add("node", shot);
        shotNode._ctx = {
          kind: "shot",
          episode: episode,
          sequence: sequence,
          shot: shot
        };

        for (var t = 0; t < SHOT_TASKS.length; t++) {
          var task = SHOT_TASKS[t];
          var workDir = shotWorkFolder(win.ctx, episode, sequence, shot, task);
          var taskLabel = taskTreeLabel(task, workDir, shot);
          /* Leaves use type "item" so AE renders them correctly under shot nodes */
          var taskNode = shotNode.add("item", taskLabel);
          var taskCtx = {
            kind: "task",
            episode: episode,
            sequence: sequence,
            shot: shot,
            task: task
          };
          var selectId = taskSelectId(episode, sequence, shot, task);
          taskNode._ctx = taskCtx;
          taskNode._selectId = selectId;
          try {
            taskNode.helpTip = selectId;
          } catch (tipErr) {
            /* helpTip not supported on this host */
          }
          win._ctxById[selectId] = taskCtx;
          win._taskNodeRegistry.push({ node: taskNode, ctx: taskCtx, id: selectId });
        }
      }
    }
  }
  if (episodesRoot.items && episodesRoot.items.length > 0) {
    episodesRoot.expanded = true;
  }
}

function restoreTreeSelection(win, path) {
  if (!path || !win.tree || !win.tree.items) {
    return;
  }
  var parts = String(path).split("/");
  if (parts.length !== 5 || parts[0] !== "shot") {
    return;
  }
  var episode = parts[1];
  var sequence = parts[2];
  var shot = parts[3];
  var task = parts[4];

  var episodesRoot = findChildByText(win.tree, "episodes");
  if (!episodesRoot) {
    return;
  }
  var episodeNode = findChildByText(episodesRoot, episode);
  if (!episodeNode) {
    return;
  }
  var sequenceNode = findChildByText(episodeNode, sequence);
  if (!sequenceNode) {
    return;
  }
  var shotNode = findShotNode(sequenceNode, shot);
  if (!shotNode) {
    return;
  }
  var taskNode = findTaskNode(shotNode, task);
  if (!taskNode) {
    return;
  }
  win.tree.selection = taskNode;
  if (taskNode._selectId && win._ctxById[taskNode._selectId]) {
    win._selection = win._ctxById[taskNode._selectId];
  } else if (taskNode._ctx) {
    win._selection = taskNode._ctx;
  }
}

function projectIsModified() {
  if (!app.project) {
    return false;
  }
  try {
    if (app.project.saved === false) {
      return true;
    }
  } catch (e1) {
    /* older hosts */
  }
  try {
    return app.project.dirty === true;
  } catch (e2) {
    return false;
  }
}

// ---------------------------------------------------------------------------
// UI

function buildPublisherWindow() {
  var ctx = resolveStudioContext();
  var win = new Window(
    "palette",
    "Workfile Publisher - " + ctx.show,
    undefined,
    { resizeable: true }
  );
  win.orientation = "column";
  win.alignChildren = ["fill", "top"];
  win.spacing = 8;
  win.margins = 12;
  win.preferredSize = [980, 620];
  win.ctx = ctx;
  win._entries = [];
  win._selection = null;
  win._taskNodeRegistry = [];
  win._ctxById = {};
  win._activeSelectId = null;
  win._updating = false;

  // Header strip
  var header = win.add("panel", undefined, undefined);
  header.orientation = "row";
  header.alignChildren = ["left", "center"];
  header.margins = 10;
  header.add("statictext", undefined, "Show: " + ctx.show);
  header.add("statictext", undefined, "Host: After Effects");
  header.add("statictext", undefined, "User: " + ctx.username);
  header.add("statictext", undefined, "Drive: " + ctx.baseShowDir);

  // Body: left tree + right panel
  var body = win.add("group");
  body.orientation = "row";
  body.alignChildren = ["fill", "fill"];
  body.alignment = ["fill", "fill"];

  var leftPanel = body.add("panel", undefined, undefined);
  leftPanel.orientation = "column";
  leftPanel.alignChildren = ["fill", "top"];
  leftPanel.preferredSize.width = 240;
  leftPanel.margins = 8;
  leftPanel.add("statictext", undefined, "Show");
  win.tree = leftPanel.add("treeview");
  win.tree.preferredSize = [220, 420];

  var rightPanel = body.add("group");
  rightPanel.orientation = "column";
  rightPanel.alignChildren = ["fill", "top"];
  rightPanel.alignment = ["fill", "fill"];

  var tableWrap = rightPanel.add("panel", undefined, "Workfiles");
  tableWrap.orientation = "column";
  tableWrap.alignChildren = ["fill", "top"];
  tableWrap.margins = 8;
  tableWrap.alignment = ["fill", "fill"];
  var tableHeader = tableWrap.add("group");
  tableHeader.orientation = "row";
  tableHeader.add("statictext", undefined, padCol("Variant", 10));
  tableHeader.add("statictext", undefined, padCol("Version", 8));
  tableHeader.add("statictext", undefined, padCol("Filename", 36));
  tableHeader.add("statictext", undefined, "Modified");
  win.table = tableWrap.add("listbox", undefined, undefined, {
    multiselect: false,
    numberOfColumns: 1,
    showHeaders: false
  });
  win.table.preferredSize = [-1, 320];
  win.table.minimumSize.height = 200;

  var actions = rightPanel.add("group");
  actions.orientation = "row";
  actions.alignChildren = ["left", "center"];
  actions.spacing = 8;
  actions.add("statictext", undefined, "Variant:");
  win.variantEdit = actions.add("edittext", undefined, "main");
  win.variantEdit.characters = 16;
  win.variantEdit.preferredSize = [120, 24];
  win.refreshBtn = actions.add("button", undefined, "Refresh");
  win.openBtn = actions.add("button", undefined, "Open Selected");
  win.publishBtn = actions.add("button", undefined, "Publish");

  win.statusBar = win.add("statictext", undefined, "Ready.");
  win.statusBar.alignment = ["fill", "top"];

  attachPublisherHandlers(win);
  win.reloadTree(false);
  if (win.layout) {
    win.layout.layout(true);
  }
  return win;
}

function attachPublisherHandlers(win) {
  win.setStatus = function (text) {
    win.statusBar.text = String(text);
  };

  win.currentShotContext = function () {
    if (!win._selection || win._selection.kind !== "task") {
      return null;
    }
    return win._selection;
  };

  win.workFolder = function () {
    var c = win.currentShotContext();
    if (!c) {
      return null;
    }
    return shotWorkFolder(win.ctx, c.episode, c.sequence, c.shot, c.task);
  };

  win.selectedEntry = function () {
    if (!win._entries || win._entries.length === 0) {
      return null;
    }
    if (!win.table || win.table.selection === null) {
      return win._entries[0];
    }
    var sel = win.table.selection;
    var idx = 0;
    if (sel && typeof sel.index === "number") {
      idx = sel.index;
    } else if (typeof sel === "number") {
      idx = sel;
    } else if (win.table.items) {
      for (var i = 0; i < win.table.items.length; i++) {
        if (win.table.items[i] === sel) {
          idx = i;
          break;
        }
      }
    }
    if (idx < 0 || idx >= win._entries.length) {
      return null;
    }
    return win._entries[idx];
  };

  win.clearTable = function () {
    win._entries = [];
    win.table.removeAll();
    win.openBtn.enabled = false;
  };

  win.populateTable = function (entries) {
    win._entries = entries || [];
    win.table.removeAll();

    for (var i = 0; i < win._entries.length; i++) {
      var e = win._entries[i];
      var row =
        e.variant +
        "  |  v" +
        padVersion(e.version) +
        "  |  " +
        e.filename +
        "  |  " +
        e.modified;
      win.table.add("item", row);
    }

    if (win._entries.length > 0) {
      try {
        if (win.table.items && win.table.items.length > 0) {
          win.table.selection = win.table.items[0];
        } else {
          win.table.selection = 0;
        }
      } catch (selErr) {
        win.table.selection = 0;
      }
      win.openBtn.enabled = true;
    } else {
      win.openBtn.enabled = false;
    }

    if (win.layout) {
      win.layout.layout(true);
    }
  };

  win.reloadTree = function (keepSelection) {
    var path = keepSelection ? treeSelectionPath(win._selection) : null;
    win._updating = true;
    try {
      populateWorkfileTree(win);
      if (path) {
        restoreTreeSelection(win, path);
      }
    } finally {
      win._updating = false;
    }
    win.refreshTable();
  };

  win.refreshTable = function () {
    var c = win.currentShotContext();
    if (!c && win._activeSelectId && win._ctxById[win._activeSelectId]) {
      c = win._ctxById[win._activeSelectId];
      win._selection = c;
    }
    if (!c) {
      win.clearTable();
      win.publishBtn.enabled = false;
      win.setStatus("Select a task in the show tree (e.g. episodes > episode > sequence > shot > layout).");
      return;
    }

    var variant;
    try {
      variant = cleanVariant(win.variantEdit.text);
    } catch (variantErr) {
      win.clearTable();
      win.publishBtn.enabled = false;
      win.setStatus(String(variantErr));
      return;
    }

    var folder = win.workFolder();
    var entries = scanAllWorkfiles(folder, c.shot, c.task);
    win.populateTable(entries);
    win.publishBtn.enabled = true;

    var nextVer = nextVersionForVariant(folder, c.shot, c.task, variant);
    if (entries.length === 0 && folder.exists) {
      var raw = folder.getFiles("*.aep");
      var rawCount = 0;
      if (raw) {
        if (raw instanceof Array) {
          rawCount = raw.length;
        } else {
          rawCount = 1;
        }
      }
      if (rawCount > 0) {
        win.setStatus(
          rawCount +
            " .aep file(s) in folder but none match *_" +
            c.task +
            "_<variant>_v###.aep — check filenames."
        );
        return;
      }
    }
    win.setStatus(
      entries.length +
        " workfile(s) in " +
        folder.fsName +
        " - next " +
        variant +
        " publish: v" +
        padVersion(nextVer)
    );
  };

  win.onPublish = function () {
    var c = win.currentShotContext();
    if (!c) {
      alert("Select a task in the show tree before publishing.");
      return;
    }

    var variant;
    try {
      variant = cleanVariant(win.variantEdit.text);
    } catch (variantErr) {
      alert(String(variantErr));
      return;
    }

    if (!app.project) {
      alert("No active After Effects project.");
      return;
    }

    var folder = win.workFolder();
    if (!ensureFolder(folder)) {
      alert("Could not create workfile folder:\n" + folder.fsName);
      return;
    }

    var version = nextVersionForVariant(folder, c.shot, c.task, variant);
    var target = buildShotFile(
      win.ctx,
      c.episode,
      c.sequence,
      c.shot,
      c.task,
      variant,
      version
    );

    if (
      !confirm(
        "Publish AE workfile v" +
          padVersion(version) +
          "?\n\n" +
          target.fsName
      )
    ) {
      return;
    }

    try {
      app.project.save(target);
    } catch (saveErr) {
      alert("Publish failed:\n" + saveErr.toString());
      return;
    }

    win.setStatus("Published " + target.fsName);
    alert("Published:\n" + target.fsName);
    win.reloadTree(true);
  };

  win.onOpenSelected = function () {
    var entry = win.selectedEntry();
    if (!entry) {
      alert("Select a workfile row to open.");
      return;
    }
    win.openEntry(entry);
  };

  win.openEntry = function (entry) {
    var file = entry.path;
    if (!file || !file.exists) {
      alert("File not found:\n" + (file ? file.fsName : ""));
      return;
    }

    if (
      app.project &&
      app.project.file &&
      app.project.file.fsName === file.fsName
    ) {
      win.setStatus("Already open: " + file.fsName);
      return;
    }

    if (projectIsModified()) {
      if (
        !confirm(
          "The current project has unsaved changes. Open the selected workfile anyway?"
        )
      ) {
        return;
      }
      try {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
      } catch (closeErr) {
        alert("Could not close current project:\n" + closeErr.toString());
        return;
      }
    }

    try {
      app.open(file);
      win.setStatus("Opened " + file.fsName);
      alert("Opened:\n" + file.fsName);
    } catch (openErr) {
      alert("Open failed:\n" + openErr.toString());
    }
  };

  function onTreeInteraction() {
    if (win._updating) {
      return;
    }
    /* Do not use app.scheduleTask — AE evaluates that string in a scope where
       helpers loaded via $.evalFile are not visible (undefined function errors). */
    applyTreeSelection(win);
  }

  win.tree.onSelect = onTreeInteraction;
  win.tree.onClick = onTreeInteraction;
  win.tree.onChange = onTreeInteraction;

  win.variantEdit.onChange = function () {
    win.refreshTable();
  };

  win.refreshBtn.onClick = function () {
    win.reloadTree(true);
  };
  win.publishBtn.onClick = function () {
    win.onPublish();
  };
  win.openBtn.onClick = function () {
    win.onOpenSelected();
  };

  win.table.onChange = function () {
    win.openBtn.enabled = win.selectedEntry() !== null;
  };

  win.table.onDoubleClick = function () {
    win.onOpenSelected();
  };

  win.openBtn.enabled = false;
  win.publishBtn.enabled = false;
}

function padCol(text, width) {
  var s = String(text);
  while (s.length < width) {
    s += " ";
  }
  return s;
}
