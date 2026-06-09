/**
 * TinyStudio AE Workfile Publisher (native ExtendScript).
 *
 * Layout mirrors the Maya workfile publisher:
 *   header (show / host / user / drive)
 *   left tabbed trees (Assets | Episodes) with disk-backed task leaves
 *   right panel (workfile table, workfile type dropdown, variant, actions)
 *
 * Browse: select a task leaf. Publish: select an asset/shot + workfile type dropdown.
 * No Python subprocess or external UI.
 */

var _publisherWindow = null;

var ASSET_TASKS = ["model", "rig", "shading", "layout", "techviz"];
var SHOT_TASKS = ["layout", "lighting", "previz", "techviz"];

function tasksForKind(kind) {
  if (kind === "asset") {
    return ASSET_TASKS;
  }
  if (kind === "shot") {
    return SHOT_TASKS;
  }
  return [];
}

function show() {
  try {
    if (_publisherWindow !== null) {
      try {
        if (_publisherWindow.visible) {
          _publisherWindow.active = true;
          return;
        }
      } catch (visibleErr) {
        /* ignore */
      }
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

function tinystudioRun() {
  show();
}

// ---------------------------------------------------------------------------
// Context / path helpers

function slash(value) {
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

function cleanTopLevelName(value, label) {
  var text = String(value || "")
    .replace(/^\s+/, "")
    .replace(/\s+$/, "")
    .replace(/\s+/g, "_");
  if (!text.length) {
    throw new Error(label + " name is required.");
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(text)) {
    throw new Error(
      label +
        " name must start with a letter or number and use only letters, numbers, underscore, or dash."
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

function taskDisplayLabel(task) {
  var parts = String(task || "").split("_");
  var out = [];
  for (var i = 0; i < parts.length; i++) {
    if (parts[i].length) {
      out.push(parts[i].charAt(0).toUpperCase() + parts[i].substring(1));
    }
  }
  return out.join(" ");
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

function parseWorkfileEntry(file, prefix, task) {
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
      regexEscape(prefix) +
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

function scanAllWorkfiles(folder, prefix, task) {
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
    var entry = parseWorkfileEntry(f, prefix, task);
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

function nextVersionForVariant(folder, prefix, task, variant) {
  var highest = 0;
  var files = scanAllWorkfiles(folder, prefix, task);
  for (var i = 0; i < files.length; i++) {
    if (files[i].variant === variant && files[i].version > highest) {
      highest = files[i].version;
    }
  }
  return highest + 1;
}

function assetWorkFolder(ctx, category, asset, task) {
  return new Folder(
    ctx.showRoot +
      "/assets/" +
      category +
      "/" +
      asset +
      "/work/ae/" +
      task
  );
}

function buildAssetFile(ctx, category, asset, task, variant, version) {
  var folder = assetWorkFolder(ctx, category, asset, task);
  var name =
    asset + "_" + task + "_" + variant + "_v" + padVersion(version) + ".aep";
  return new File(folder.fsName + "/" + name);
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

function reserveWorkfilePath(win, c, variant) {
  var folder = win.workFolderFor(c);
  if (!ensureFolder(folder)) {
    throw new Error("Could not create workfile folder:\n" + folder.fsName);
  }

  var prefix = win.workfilePrefixFor(c);
  var version = nextVersionForVariant(folder, prefix, c.task, variant);
  for (var attempt = 0; attempt < 64; attempt++) {
    var target;
    if (c.kind === "asset") {
      target = buildAssetFile(
        win.ctx,
        c.category,
        c.asset,
        c.task,
        variant,
        version
      );
    } else {
      target = buildShotFile(
        win.ctx,
        c.episode,
        c.sequence,
        c.shot,
        c.task,
        variant,
        version
      );
    }

    if (!target.exists) {
      if (target.open("w")) {
        target.close();
        return target;
      }
    }
    version++;
  }

  throw new Error(
    "Could not reserve a version slot under " +
      folder.fsName +
      "; another artist may be publishing rapidly."
  );
}

function releaseReservedPath(file) {
  if (!file || !file.exists) {
    return;
  }
  try {
    if (file.length === 0) {
      file.remove();
    }
  } catch (removeErr) {
    /* best-effort cleanup */
  }
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

function taskTreeLabel(task, count) {
  return count > 1 ? task + "  (" + count + ")" : task;
}

function assetTaskSelectId(category, asset, task) {
  return "asset|" + category + "|" + asset + "|" + task;
}

function shotTaskSelectId(episode, sequence, shot, task) {
  return "shot|" + episode + "|" + sequence + "|" + shot + "|" + task;
}

function populateTaskDropdown(win, kind) {
  win.taskDropdown.removeAll();
  var tasks = tasksForKind(kind);
  for (var i = 0; i < tasks.length; i++) {
    win.taskDropdown.add("item", taskDisplayLabel(tasks[i]));
  }
  if (tasks.length > 0) {
    win.taskDropdown.selection = 0;
  }
}

function setTopLevelNameContext(win, kind) {
  if (!win.nameLabel || !win.nameEdit) {
    return;
  }

  if (kind === "asset") {
    win.nameLabel.text = "Asset name:";
    win.nameEdit.enabled = true;
    win.nameEdit.helpTip =
      "Type a new asset name or use the selected asset from the tree.";
    if (win._selection && win._selection.asset) {
      win.nameEdit.text = win._selection.asset;
    }
    return;
  }

  if (kind === "shot") {
    win.nameLabel.text = "Shot name:";
    win.nameEdit.text = "";
    win.nameEdit.enabled = false;
    win.nameEdit.helpTip = "Set by production.";
    return;
  }

  win.nameLabel.text = "Asset name:";
  win.nameEdit.text = "";
  win.nameEdit.enabled = false;
  win.nameEdit.helpTip = "";
}

function setTaskDropdownSelection(win, task, kind) {
  var tasks = tasksForKind(kind);
  for (var i = 0; i < tasks.length; i++) {
    if (tasks[i] === task) {
      win.taskDropdown.selection = i;
      return;
    }
  }
}

function resolveTreeContext(win, node) {
  if (!node) {
    return null;
  }

  if (node._ctx && node._ctx.kind === "asset") {
    return node._ctx;
  }

  if (node._ctx && node._ctx.kind === "shot") {
    return node._ctx;
  }

  if (
    node._ctx &&
    (node._ctx.kind === "category" || node._ctx.kind === "sequence")
  ) {
    return node._ctx;
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

function normalizeSelection(ctx) {
  if (!ctx) {
    return null;
  }
  if (ctx.kind === "task") {
    if (ctx.context === "asset" || ctx.category) {
      return {
        kind: "asset",
        category: ctx.category,
        asset: ctx.asset,
        task: ctx.task
      };
    }
    return {
      kind: "shot",
      episode: ctx.episode,
      sequence: ctx.sequence,
      shot: ctx.shot,
      task: ctx.task
    };
  }
  if (ctx.kind === "asset") {
    return {
      kind: "asset",
      category: ctx.category,
      asset: ctx.asset,
      task: ctx.task || null
    };
  }
  if (ctx.kind === "category") {
    return {
      kind: "asset",
      category: ctx.category,
      asset: null,
      task: null
    };
  }
  if (ctx.kind === "sequence") {
    return {
      kind: "shot",
      episode: ctx.episode,
      sequence: ctx.sequence,
      shot: null,
      task: null
    };
  }
  if (ctx.kind === "shot") {
    return {
      kind: "shot",
      episode: ctx.episode,
      sequence: ctx.sequence,
      shot: ctx.shot,
      task: ctx.task || null
    };
  }
  return null;
}

function activeTree(win) {
  if (win._activeKind === "asset") {
    return win.assetTree;
  }
  return win.shotTree;
}

function clearTreeSelection(tree) {
  if (!tree) {
    return;
  }
  try {
    tree.selection = null;
  } catch (clearErr) {
    /* ignore */
  }
}

function applyTreeSelection(win) {
  var tree = activeTree(win);
  var raw = resolveTreeContext(win, tree.selection);
  win._selection = normalizeSelection(raw);
  if (win._selection) {
    populateTaskDropdown(win, win._selection.kind);
    setTopLevelNameContext(win, win._selection.kind);
    if (win._selection.task) {
      if (win._selection.kind === "asset") {
        win._activeSelectId = assetTaskSelectId(
          win._selection.category,
          win._selection.asset,
          win._selection.task
        );
      } else {
        win._activeSelectId = shotTaskSelectId(
          win._selection.episode,
          win._selection.sequence,
          win._selection.shot,
          win._selection.task
        );
      }
      setTaskDropdownSelection(win, win._selection.task, win._selection.kind);
      win.setTaskDropdownEnabled(true);
    } else {
      win._activeSelectId = null;
      win.setTaskDropdownEnabled(true);
    }
  } else {
    win._activeSelectId = null;
    populateTaskDropdown(win, null);
    setTopLevelNameContext(win, null);
    win.setTaskDropdownEnabled(false);
  }
  win.refreshTable();
  relayoutPublisherWindow(win);
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
  if (!ctx) {
    return null;
  }
  if (ctx.kind === "asset") {
    if (ctx.task) {
      return (
        "asset/" + ctx.category + "/" + ctx.asset + "/" + ctx.task
      );
    }
    if (ctx.asset) {
      return "asset/" + ctx.category + "/" + ctx.asset;
    }
    return "asset/" + ctx.category;
  }
  if (ctx.kind === "shot") {
    if (ctx.task) {
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
    if (!ctx.shot) {
      return "shot/" + ctx.episode + "/" + ctx.sequence;
    }
    return (
      "shot/" + ctx.episode + "/" + ctx.sequence + "/" + ctx.shot
    );
  }
  return null;
}

function switchTabForPath(win, path) {
  if (!path || !win.tabs) {
    return;
  }
  if (String(path).indexOf("asset/") === 0) {
    win.tabs.selection = win.assetsTab;
    win._activeKind = "asset";
    return;
  }
  if (String(path).indexOf("shot/") === 0) {
    win.tabs.selection = win.episodesTab;
    win._activeKind = "shot";
  }
}

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

function findAssetNode(parent, asset) {
  if (!parent || !parent.items) {
    return null;
  }
  for (var i = 0; i < parent.items.length; i++) {
    var node = parent.items[i];
    if (node._ctx && node._ctx.kind === "asset" && node._ctx.asset === asset) {
      return node;
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

function registerTaskNode(win, taskNode, taskCtx, selectId) {
  taskNode._ctx = taskCtx;
  taskNode._selectId = selectId;
  try {
    taskNode.helpTip = selectId;
  } catch (tipErr) {
    /* helpTip not supported on this host */
  }
  win._ctxById[selectId] = taskCtx;
  win._taskNodeRegistry.push({
    node: taskNode,
    ctx: taskCtx,
    id: selectId
  });
}

function populateAssetTree(win) {
  clearTree(win.assetTree);
  var categories = listSubdirs(new Folder(win.ctx.showRoot + "/assets"));
  for (var c = 0; c < categories.length; c++) {
    var category = categories[c];
    var categoryNode = addFolderNode(win.assetTree, category, "category");
    categoryNode._ctx = {
      kind: "category",
      category: category
    };
    expandTreeNode(categoryNode);
    var catFolder = new Folder(win.ctx.showRoot + "/assets/" + category);
    var assets = listSubdirs(catFolder);
    for (var a = 0; a < assets.length; a++) {
      var asset = assets[a];
      var assetNode = categoryNode.add("node", asset);
      assetNode._ctx = {
        kind: "asset",
        category: category,
        asset: asset
      };

      for (var t = 0; t < ASSET_TASKS.length; t++) {
        var task = ASSET_TASKS[t];
        var workDir = assetWorkFolder(win.ctx, category, asset, task);
        var count = scanAllWorkfiles(workDir, asset, task).length;
        if (count === 0) {
          continue;
        }
        var taskNode = assetNode.add("item", taskTreeLabel(task, count));
        var taskCtx = {
          kind: "task",
          context: "asset",
          category: category,
          asset: asset,
          task: task
        };
        registerTaskNode(
          win,
          taskNode,
          taskCtx,
          assetTaskSelectId(category, asset, task)
        );
      }
    }
  }
}

function populateShotTree(win) {
  clearTree(win.shotTree);
  var episodes = listSubdirs(new Folder(win.ctx.showRoot + "/episodes"));
  for (var e = 0; e < episodes.length; e++) {
    var episode = episodes[e];
    var episodeNode = addFolderNode(win.shotTree, episode, "episode");
    expandTreeNode(episodeNode);
    var seqFolder = new Folder(win.ctx.showRoot + "/episodes/" + episode);
    var sequences = listSubdirs(seqFolder);
    for (var s = 0; s < sequences.length; s++) {
      var sequence = sequences[s];
      var sequenceNode = addFolderNode(episodeNode, sequence, "sequence");
      sequenceNode._ctx = {
        kind: "sequence",
        episode: episode,
        sequence: sequence
      };
      expandTreeNode(sequenceNode);
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
          var count = scanAllWorkfiles(workDir, shot, task).length;
          if (count === 0) {
            continue;
          }
          var taskNode = shotNode.add("item", taskTreeLabel(task, count));
          var taskCtx = {
            kind: "task",
            context: "shot",
            episode: episode,
            sequence: sequence,
            shot: shot,
            task: task
          };
          registerTaskNode(
            win,
            taskNode,
            taskCtx,
            shotTaskSelectId(episode, sequence, shot, task)
          );
        }
      }
    }
  }
}

function populateWorkfileTrees(win) {
  win._selection = null;
  win._taskNodeRegistry = [];
  win._ctxById = {};
  populateAssetTree(win);
  populateShotTree(win);
}

function expandTreeNode(node) {
  if (!node) {
    return;
  }
  try {
    node.expanded = true;
  } catch (expandErr) {
    /* expanded not supported on this node type */
  }
}

function restoreAssetSelection(win, path) {
  var parts = String(path).split("/");
  if (parts[0] !== "asset" || parts.length < 2 || parts.length > 4) {
    return;
  }
  var category = parts[1];
  var asset = parts.length >= 3 ? parts[2] : null;
  var task = parts.length === 4 ? parts[3] : null;
  var tree = win.assetTree;

  var categoryNode = findChildByText(tree, category);
  if (!categoryNode) {
    return;
  }
  expandTreeNode(categoryNode);
  if (!asset) {
    tree.selection = categoryNode;
    win._selection = normalizeSelection(categoryNode._ctx);
    populateTaskDropdown(win, "asset");
    setTopLevelNameContext(win, "asset");
    win.setTaskDropdownEnabled(true);
    return;
  }
  var assetNode = findAssetNode(categoryNode, asset);
  if (!assetNode) {
    return;
  }

  expandTreeNode(assetNode);

  if (task) {
    var taskNode = findTaskNode(assetNode, task);
    var assetCtx = {
      kind: "asset",
      category: category,
      asset: asset,
      task: task
    };
    if (taskNode) {
      tree.selection = taskNode;
      if (taskNode._selectId && win._ctxById[taskNode._selectId]) {
        win._selection = normalizeSelection(win._ctxById[taskNode._selectId]);
      } else if (taskNode._ctx) {
        win._selection = normalizeSelection(taskNode._ctx);
      } else {
        win._selection = assetCtx;
      }
    } else {
      tree.selection = assetNode;
      win._selection = assetCtx;
    }
    populateTaskDropdown(win, "asset");
    setTopLevelNameContext(win, "asset");
    setTaskDropdownSelection(win, task, "asset");
    win.setTaskDropdownEnabled(true);
    return;
  }

  tree.selection = assetNode;
  win._selection = normalizeSelection(assetNode._ctx);
  populateTaskDropdown(win, "asset");
  setTopLevelNameContext(win, "asset");
  win.setTaskDropdownEnabled(true);
}

function restoreShotSelection(win, path) {
  var parts = String(path).split("/");
  if (parts[0] !== "shot" || parts.length < 3 || parts.length > 5) {
    return;
  }
  var episode = parts[1];
  var sequence = parts[2];
  var shot = parts.length >= 4 ? parts[3] : null;
  var task = parts.length === 5 ? parts[4] : null;
  var tree = win.shotTree;

  var episodeNode = findChildByText(tree, episode);
  if (!episodeNode) {
    return;
  }
  var sequenceNode = findChildByText(episodeNode, sequence);
  if (!sequenceNode) {
    return;
  }
  expandTreeNode(episodeNode);
  expandTreeNode(sequenceNode);
  if (!shot) {
    tree.selection = sequenceNode;
    win._selection = normalizeSelection(sequenceNode._ctx);
    populateTaskDropdown(win, "shot");
    setTopLevelNameContext(win, "shot");
    win.setTaskDropdownEnabled(true);
    return;
  }
  var shotNode = findShotNode(sequenceNode, shot);
  if (!shotNode) {
    return;
  }

  expandTreeNode(shotNode);

  if (task) {
    var taskNode = findTaskNode(shotNode, task);
    var shotCtx = {
      kind: "shot",
      episode: episode,
      sequence: sequence,
      shot: shot,
      task: task
    };
    if (taskNode) {
      tree.selection = taskNode;
      if (taskNode._selectId && win._ctxById[taskNode._selectId]) {
        win._selection = normalizeSelection(win._ctxById[taskNode._selectId]);
      } else if (taskNode._ctx) {
        win._selection = normalizeSelection(taskNode._ctx);
      } else {
        win._selection = shotCtx;
      }
    } else {
      tree.selection = shotNode;
      win._selection = shotCtx;
    }
    populateTaskDropdown(win, "shot");
    setTopLevelNameContext(win, "shot");
    setTaskDropdownSelection(win, task, "shot");
    win.setTaskDropdownEnabled(true);
    return;
  }

  tree.selection = shotNode;
  win._selection = normalizeSelection(shotNode._ctx);
  populateTaskDropdown(win, "shot");
  setTopLevelNameContext(win, "shot");
  win.setTaskDropdownEnabled(true);
}

function restoreTreeSelection(win, path) {
  if (!path) {
    return;
  }
  switchTabForPath(win, path);
  if (String(path).indexOf("asset/") === 0) {
    restoreAssetSelection(win, path);
    return;
  }
  if (String(path).indexOf("shot/") === 0) {
    restoreShotSelection(win, path);
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

function confirmPublishPath(file) {
  return confirm(
    "Publish this workfile?\n\nThe workfile will be saved here:\n\n" +
      file.fsName
  );
}

// ---------------------------------------------------------------------------
// UI

function relayoutPublisherWindow(win, rebuild) {
  if (win && win.layout) {
    if (rebuild) {
      win.layout.layout(true);
    }
    if (win.layout.resize) {
      win.layout.resize();
    }
  }
}

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
  win.preferredSize = [1200, 620];
  win.minimumSize = [900, 480];
  win.ctx = ctx;
  win._entries = [];
  win._selection = null;
  win._taskNodeRegistry = [];
  win._ctxById = {};
  win._activeSelectId = null;
  win._updating = false;

  var header = win.add("panel", undefined, undefined);
  header.orientation = "row";
  header.alignChildren = ["left", "center"];
  header.alignment = ["fill", "top"];
  header.margins = 10;
  header.add("statictext", undefined, "Show: " + ctx.show);
  header.add("statictext", undefined, "Host: After Effects");
  header.add("statictext", undefined, "User: " + ctx.username);
  header.add("statictext", undefined, "Drive: " + ctx.baseShowDir);

  var body = win.add("group");
  body.orientation = "row";
  body.alignChildren = ["fill", "fill"];
  body.alignment = ["fill", "fill"];

  var leftPanel = body.add("panel", undefined, undefined);
  leftPanel.orientation = "column";
  leftPanel.alignChildren = ["fill", "fill"];
  leftPanel.alignment = ["left", "fill"];
  leftPanel.preferredSize = [480, 420];
  leftPanel.margins = 8;
  win.tabs = leftPanel.add("tabbedpanel");
  win.tabs.preferredSize = [440, 420];
  win.tabs.alignChildren = ["fill", "fill"];
  win.tabs.alignment = ["fill", "fill"];
  win.assetsTab = win.tabs.add("tab", undefined, "Assets");
  win.episodesTab = win.tabs.add("tab", undefined, "Episodes");
  win.assetsTab.alignChildren = ["fill", "fill"];
  win.episodesTab.alignChildren = ["fill", "fill"];
  win.assetTree = win.assetsTab.add("treeview");
  win.shotTree = win.episodesTab.add("treeview");
  win.assetTree.preferredSize = [420, 380];
  win.shotTree.preferredSize = [420, 380];
  win.assetTree.alignment = ["fill", "fill"];
  win.shotTree.alignment = ["fill", "fill"];
  win._activeKind = "asset";
  win.tabs.selection = win.assetsTab;

  var rightPanel = body.add("group");
  rightPanel.orientation = "column";
  rightPanel.alignChildren = ["fill", "fill"];
  rightPanel.alignment = ["fill", "fill"];

  var tableWrap = rightPanel.add("panel", undefined, "Workfiles");
  tableWrap.orientation = "column";
  tableWrap.alignChildren = ["fill", "fill"];
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
  win.table.preferredSize = [620, 320];
  win.table.minimumSize = [320, 200];
  win.table.alignment = ["fill", "fill"];

  var actions = rightPanel.add("group");
  actions.orientation = "column";
  actions.alignChildren = ["fill", "top"];
  actions.alignment = ["fill", "bottom"];
  actions.spacing = 8;

  var formRow = actions.add("group");
  formRow.orientation = "row";
  formRow.alignChildren = ["left", "center"];
  formRow.spacing = 8;
  win.nameLabel = formRow.add("statictext", undefined, "Asset name:");
  win.nameEdit = formRow.add("edittext", undefined, "");
  win.nameEdit.characters = 24;
  win.nameEdit.preferredSize = [180, 24];
  win.nameEdit.enabled = false;
  formRow.add("statictext", undefined, "Variant:");
  win.variantEdit = formRow.add("edittext", undefined, "main");
  win.variantEdit.characters = 16;
  win.variantEdit.preferredSize = [120, 24];

  var typeRow = actions.add("group");
  typeRow.orientation = "row";
  typeRow.alignChildren = ["left", "center"];
  typeRow.spacing = 8;
  typeRow.add("statictext", undefined, "Workfile type:");
  win.taskDropdown = typeRow.add("dropdownlist", undefined, []);
  win.taskDropdown.preferredSize = [260, 24];
  populateTaskDropdown(win, null);
  win.taskDropdown.enabled = false;

  var buttonRow = actions.add("group");
  buttonRow.orientation = "row";
  buttonRow.alignChildren = ["left", "center"];
  buttonRow.spacing = 8;
  buttonRow.alignment = ["right", "center"];
  win.refreshBtn = buttonRow.add("button", undefined, "Refresh");
  win.openBtn = buttonRow.add("button", undefined, "Open Selected");
  win.publishBtn = buttonRow.add("button", undefined, "Publish");

  win.statusBar = win.add("statictext", undefined, "Ready.");
  win.statusBar.alignment = ["fill", "bottom"];

  win.onResize = function () {
    relayoutPublisherWindow(win, false);
  };
  win.onResizing = win.onResize;
  win.onShow = function () {
    relayoutPublisherWindow(win, true);
  };

  attachPublisherHandlers(win);
  win.reloadTree(false);
  relayoutPublisherWindow(win, true);
  return win;
}

function attachPublisherHandlers(win) {
  win.setStatus = function (text) {
    win.statusBar.text = String(text);
  };

  win.setTaskDropdownEnabled = function (enabled) {
    win.taskDropdown.enabled = !!enabled;
  };

  win.currentTaskFromDropdown = function () {
    if (!win.taskDropdown || !win.taskDropdown.enabled) {
      return "";
    }
    var kind =
      win._selection && win._selection.kind
        ? win._selection.kind
        : win._activeKind;
    var tasks = tasksForKind(kind);
    var sel = win.taskDropdown.selection;
    var idx = 0;
    if (sel && typeof sel.index === "number") {
      idx = sel.index;
    } else if (typeof sel === "number") {
      idx = sel;
    }
    if (idx < 0 || idx >= tasks.length) {
      return "";
    }
    return tasks[idx];
  };

  win.browseContext = function () {
    if (!win._selection || !win._selection.task) {
      return null;
    }
    if (win._selection.kind !== "asset" && win._selection.kind !== "shot") {
      return null;
    }
    return win._selection;
  };

  win.publishContext = function () {
    if (
      !win._selection ||
      (win._selection.kind !== "asset" && win._selection.kind !== "shot")
    ) {
      return null;
    }
    var task = win._selection.task || win.currentTaskFromDropdown();
    if (!task) {
      return null;
    }
    if (win._selection.kind === "asset") {
      var assetName;
      try {
        assetName = win._selection.asset || cleanTopLevelName(win.nameEdit.text, "Asset");
      } catch (assetErr) {
        return null;
      }
      return {
        kind: "asset",
        category: win._selection.category,
        asset: assetName,
        task: task
      };
    }
    if (!win._selection.shot) {
      return null;
    }
    return {
      kind: "shot",
      episode: win._selection.episode,
      sequence: win._selection.sequence,
      shot: win._selection.shot,
      task: task
    };
  };

  win.workFolderFor = function (c) {
    if (!c || !c.task) {
      return null;
    }
    if (c.kind === "asset") {
      return assetWorkFolder(win.ctx, c.category, c.asset, c.task);
    }
    if (c.kind === "shot") {
      return shotWorkFolder(win.ctx, c.episode, c.sequence, c.shot, c.task);
    }
    return null;
  };

  win.workfilePrefixFor = function (c) {
    if (!c) {
      return "";
    }
    if (c.kind === "asset") {
      return c.asset;
    }
    if (c.kind === "shot") {
      return c.shot;
    }
    return "";
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

    relayoutPublisherWindow(win);
  };

  win.reloadTree = function (keepSelection, restorePathOverride) {
    var path = restorePathOverride || null;
    var pendingAssetName = null;
    if (!path && keepSelection) {
      path = treeSelectionPath(win._selection);
      if (
        win._selection &&
        win._selection.kind === "asset" &&
        !win._selection.asset &&
        win.nameEdit &&
        win.nameEdit.enabled
      ) {
        pendingAssetName = win.nameEdit.text;
      }
    }
    win._updating = true;
    try {
      populateWorkfileTrees(win);
      if (path) {
        restoreTreeSelection(win, path);
      }
      if (
        pendingAssetName &&
        win._selection &&
        win._selection.kind === "asset" &&
        !win._selection.asset
      ) {
        win.nameEdit.text = pendingAssetName;
      }
    } finally {
      win._updating = false;
    }
    win.refreshTable();
  };

  win.refreshTable = function () {
    var browse = win.browseContext();
    var publish = win.publishContext();

    if (!publish) {
      win.clearTable();
      win.publishBtn.enabled = false;
      win.setTaskDropdownEnabled(
        !!win._selection &&
          (win._selection.kind === "asset" || win._selection.kind === "shot")
      );
      if (!win._selection) {
        win.setStatus(
          "Select a category in Assets or a production-created shot in Episodes."
        );
      } else if (win._selection.kind === "asset" && !win._selection.asset) {
        win.setStatus(
          "Set asset name, workfile type, and variant to publish."
        );
      } else if (win._selection.kind === "shot" && !win._selection.shot) {
        win.setStatus(
          "Select a production-created shot in the tree before publishing."
        );
      } else {
        win.setStatus("Select a workfile type before publishing.");
      }
      return;
    }

    win.setTaskDropdownEnabled(true);

    var variant;
    try {
      variant = cleanVariant(win.variantEdit.text);
    } catch (variantErr) {
      win.clearTable();
      win.publishBtn.enabled = false;
      win.setStatus(String(variantErr));
      return;
    }

    win.publishBtn.enabled = true;

    if (!browse) {
      win.clearTable();
      if (win._selection && !win._selection.task) {
        if (win._selection.kind === "asset" && !win._selection.asset) {
          win.setStatus(
            "Set asset name, workfile type, and variant to publish, or select a workfile type in the tree to browse versions."
          );
        } else {
          win.setStatus(
            "Select a workfile type in the tree to browse versions, or pick a type below to publish."
          );
        }
      } else {
        win.setStatus(
          "Select a workfile type in the tree, or pick a type below to publish."
        );
      }
      return;
    }

    var folder = win.workFolderFor(browse);
    var prefix = win.workfilePrefixFor(browse);
    var entries = scanAllWorkfiles(folder, prefix, browse.task);
    win.populateTable(entries);

    var nextVer = nextVersionForVariant(folder, prefix, browse.task, variant);
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
            browse.task +
            "_<variant>_v###.aep - check filenames."
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
    var c = win.publishContext();
    if (!c) {
      if (!win._selection) {
        alert("Select an asset category or production-created shot before publishing.");
      } else if (win._selection.kind === "asset" && !win._selection.asset) {
        try {
          cleanTopLevelName(win.nameEdit.text, "Asset");
        } catch (assetErr) {
          alert(String(assetErr));
          return;
        }
        alert("Select a workfile type before publishing.");
      } else if (win._selection.kind === "shot" && !win._selection.shot) {
        alert("Select a production-created shot before publishing.");
      } else {
        alert("Select a workfile type before publishing.");
      }
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

    var target;
    try {
      target = reserveWorkfilePath(win, c, variant);
    } catch (reserveErr) {
      alert("Could not reserve publish path:\n" + reserveErr.toString());
      return;
    }

    if (!confirmPublishPath(target)) {
      releaseReservedPath(target);
      win.setStatus("Publish cancelled.");
      return;
    }

    try {
      app.project.save(target);
    } catch (saveErr) {
      releaseReservedPath(target);
      alert("Publish failed:\n" + saveErr.toString());
      return;
    }

    var restorePath;
    if (c.kind === "asset") {
      restorePath =
        "asset/" + c.category + "/" + c.asset + "/" + c.task;
    } else {
      restorePath =
        "shot/" +
        c.episode +
        "/" +
        c.sequence +
        "/" +
        c.shot +
        "/" +
        c.task;
    }
    win.setStatus("Published " + target.fsName);
    win.reloadTree(true, restorePath);
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
    } catch (openErr) {
      alert("Open failed:\n" + openErr.toString());
    }
  };

  function onAssetTreeInteraction() {
    if (win._updating) {
      return;
    }
    win._activeKind = "asset";
    if (win.tabs && win.assetsTab) {
      win.tabs.selection = win.assetsTab;
    }
    applyTreeSelection(win);
  }

  function onShotTreeInteraction() {
    if (win._updating) {
      return;
    }
    win._activeKind = "shot";
    if (win.tabs && win.episodesTab) {
      win.tabs.selection = win.episodesTab;
    }
    applyTreeSelection(win);
  }

  win.assetTree.onSelect = onAssetTreeInteraction;
  win.assetTree.onClick = onAssetTreeInteraction;
  win.assetTree.onChange = onAssetTreeInteraction;

  win.shotTree.onSelect = onShotTreeInteraction;
  win.shotTree.onClick = onShotTreeInteraction;
  win.shotTree.onChange = onShotTreeInteraction;

  win.tabs.onChange = function () {
    if (win._updating) {
      return;
    }
    if (win.tabs.selection === win.assetsTab) {
      win._activeKind = "asset";
      clearTreeSelection(win.shotTree);
    } else {
      win._activeKind = "shot";
      clearTreeSelection(win.assetTree);
    }
    applyTreeSelection(win);
  };

  win.taskDropdown.onChange = function () {
    win.refreshTable();
  };

  win.variantEdit.onChange = function () {
    win.refreshTable();
  };

  win.nameEdit.onChange = function () {
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
