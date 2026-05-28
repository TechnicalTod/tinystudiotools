/**
 * TinyStudio Tools — ScriptUI Panel (Window menu)
 *
 * Registry: manifest JSON (default {AE_REPO}/config/tinystudio_ae_tools.json).
 *   Override with AE_MANIFEST absolute path if needed.
 *
 * Tool contract: each tool .jsx loaded via $.evalFile must define:
 *   function tinystudioRun() { ... }
 *
 * Launch After Effects from TinyStudioLauncher so AE_REPO is set, or set AE_REPO
 * manually to your AERepository root. Run install_tinystudio_ae_panel.ps1 once
 * so this file appears under Adobe ScriptUI Panels.
 */
(function (thisObj) {
  var MANIFEST_REL = "config/tinystudio_ae_tools.json";

  function repoRoot() {
    var r = $.getenv("AE_REPO");
    if (r && String(r).length) {
      return new Folder(String(r)).fsName;
    }
    return "";
  }

  function manifestFullPath(root) {
    var envM = $.getenv("AE_MANIFEST");
    if (envM && String(envM).length) {
      return new File(String(envM)).fsName;
    }
    return new File(root + "/" + MANIFEST_REL).fsName;
  }

  function readTextFile(filePath) {
    var f = new File(filePath);
    if (!f.exists) {
      return null;
    }
    f.encoding = "UTF-8";
    if (!f.open("r")) {
      return null;
    }
    var txt = f.read();
    f.close();
    if (txt === null || txt === undefined) {
      return null;
    }
    txt = String(txt);
    // UTF-8 BOM breaks JSON.parse in many ExtendScript builds
    if (txt.length && txt.charCodeAt(0) === 0xfeff) {
      txt = txt.substring(1);
    }
    return txt.replace(/^\s+/, "").replace(/\s+$/, "");
  }

  /**
   * Parse trusted local manifest. JSON.parse may fail on BOM/edge cases; eval fallback matches ES3 loaders.
   */
  function parseManifest(text) {
    if (!text || !String(text).length) {
      return null;
    }
    var t = String(text);
    if (typeof JSON !== "undefined" && JSON.parse) {
      try {
        return JSON.parse(t);
      } catch (e1) {
        /* fall through */
      }
    }
    try {
      return eval("(" + t + ")");
    } catch (e2) {
      return null;
    }
  }

  function buildUI(thisObj) {
    var pal =
      thisObj instanceof Panel
        ? thisObj
        : new Window("palette", "TinyStudio Tools", undefined, { resizeable: true });

    var root = repoRoot();
    var tools = [];
    var errMsg = "";

    if (!root) {
      errMsg =
        "AE_REPO is not set.\n\nLaunch from TinyStudio Launcher, or set AE_REPO to your AERepository folder.";
    } else {
      var mpath = manifestFullPath(root);
      var mtext = readTextFile(mpath);
      if (!mtext) {
        errMsg = "Could not read manifest:\n" + mpath;
      } else {
        var data = parseManifest(mtext);
        if (!data || !data.tools) {
          errMsg = "Invalid manifest JSON:\n" + mpath;
        } else {
          for (var i = 0; i < data.tools.length; i++) {
            var t = data.tools[i];
            if (t && t.enabled !== false && t.label && t.script) {
              tools.push(t);
            }
          }
          if (tools.length === 0) {
            errMsg = "No enabled tools in manifest.";
          }
        }
      }
    }

    pal.orientation = "column";
    pal.alignChildren = ["fill", "top"];
    pal.spacing = 6;
    pal.margins = 10;

    var stStatus = pal.add("statictext", undefined, "", { multiline: true });
    stStatus.preferredSize = [240, 56];

    if (errMsg) {
      stStatus.text = errMsg;
      if (pal instanceof Window) {
        var btn = pal.add("button", undefined, "Close");
        btn.onClick = function () {
          pal.close();
        };
      }
    } else {
      stStatus.text = "Repo: " + root;

      var dd = pal.add("dropdownlist");
      dd.preferredSize = [240, 26];
      for (var j = 0; j < tools.length; j++) {
        dd.add("item", tools[j].label);
      }
      if (dd.items.length > 0) {
        dd.selection = 0;
      }

      var row = pal.add("group");
      row.orientation = "row";
      row.alignChildren = ["fill", "center"];

      var runBtn = row.add("button", undefined, "Run");
      var refBtn = row.add("button", undefined, "Refresh");

      runBtn.onClick = function () {
        var idx = dd.selection ? dd.selection.index : 0;
        var tool = tools[idx];
        if (!tool) {
          return;
        }
        var scriptPath = new File(root + "/" + tool.script);
        if (!scriptPath.exists) {
          alert("Script missing:\n" + scriptPath.fsName);
          return;
        }
        // Avoid running a stale entry point if the selected script fails to
        // load or no longer defines tinystudioRun().
        tinystudioRun = undefined;
        try {
          $.evalFile(scriptPath);
        } catch (e) {
          alert("Error loading tool script:\n" + String(e));
          return;
        }
        if (typeof tinystudioRun !== "function") {
          alert("Tool did not define tinystudioRun():\n" + scriptPath.fsName);
          return;
        }
        try {
          tinystudioRun();
        } catch (e2) {
          alert("Tool error:\n" + String(e2));
        }
      };

      refBtn.onClick = function () {
        alert(
          "Close this panel and reopen it from the Window menu to reload the manifest from disk."
        );
      };
    }

    if (pal instanceof Window) {
      pal.layout.layout(true);
    }
    return pal;
  }

  var ui = buildUI(thisObj);
  if (ui instanceof Window) {
    ui.center();
    ui.show();
  } else {
    ui.layout.layout(true);
  }
})(this);
