"""Exercise repeated track opening against the actual browser script."""
from pathlib import Path
import shutil
import subprocess
import unittest


class TrackNavigationTests(unittest.TestCase):
    """Simulate the attribute-only DOM update used when reopening the same song."""

    @unittest.skipUnless(shutil.which("node"), "Node is required for the DOM event regression")
    def test_reopen_after_back_and_ignore_duplicate_notifications(self):
        """Closing and changing only the request marker must reopen the overlay."""
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let overlay = null, observer;
const incoming = {
  dataset: {song:'song.wav', request:'first'},
  cloneNode() {
    return {dataset:{...this.dataset}, scrollTop:0, handlers:{},
      remove(){overlay=null}, querySelector(){return {focus(){}}},
      addEventListener(type, fn){this.handlers[type]=fn}};
  }
};
const context = {
  element:{querySelector(){return incoming}}, trigger(){},
  document:{body:{appendChild(node){overlay=node}}, querySelectorAll(){return []}},
  MutationObserver:class {
    constructor(callback){this.callback=callback; observer=this}
    observe(element, options){this.options=options}
  }
};
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), context);
assert.ok(overlay);
overlay.handlers.click({target:{closest(selector){return selector==='[data-close]'?{}:null}}});
assert.equal(overlay,null);
incoming.dataset.request='second';
if(observer.options.attributes && observer.options.attributeFilter.includes('data-request')) observer.callback();
assert.ok(overlay, 'same-song attribute update must reopen the page');
const reopened=overlay;
observer.callback();
assert.equal(overlay,reopened, 'duplicate notifications must preserve the open page');
"""
        result = subprocess.run([shutil.which("node"), "-e", script,
                                 str(Path(__file__).with_name("library_track_view.js"))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
