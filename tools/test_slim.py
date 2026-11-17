"""Offline regression tests; pip install lupa. No device writes."""
import base64
import re
import subprocess
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
lua = LuaRuntime(unpack_returned_tuples=True)
compile_lua = lua.eval("function(s,n) local f,e=load(s,n); assert(f,e); return true end")
for path in APP.rglob("*.lua"):
    compile_lua(path.read_text(encoding="utf-8"), str(path))
print("PASS: all Lua files compile")

for removed in ["assets/skins/whale", "assets/whale", "assets/skins/pc2005/slow",
                "assets/skins/pc2005/fast", "assets/skins/pc2005/mirror/slow",
                "assets/skins/pc2005/mirror/fast"]:
    assert not (APP / removed).exists(), removed
assert len(list((APP / "assets/skins/pc2005/normal").glob("*.gif"))) == 114
assert len(list((APP / "assets/skins/pc2005/meme/normal").glob("*.gif"))) == 114
assert len(list((APP / "assets/skins/pc2005/mirror/normal").glob("*.gif"))) == 3

lua.execute("file={exists=function() return true end,getcontents=function() return nil end}")
skin = lua.execute((APP / "skin.lua").read_text(encoding="utf-8"))
manifest = lua.execute((APP / "assets/skins/pc2005/manifest.lua").read_text(encoding="utf-8"))
state = skin.load_state("/sd/apps/renamed_pet")
assert state.active == "pc2005" and state.speed == "normal"
lua.execute('file.getcontents=function() return "old" end; sjson={decode=function() return {active="whale",speed="fast",behavior={variants={obsolete=true}}} end}')
state = skin.load_state("/sd/apps/renamed_pet")
assert state.active == "pc2005" and state.speed == "normal"
assert state.behavior.variants.obsolete is None
for speed in ["normal", "fast", "slow"]:
    pack = skin.resolve(manifest, "/sd/apps/renamed_pet/assets/skins/pc2005", speed)
    assert pack.speed == "normal" and len(pack.moves) == 3 and len(pack.turn) == 1
    paths = [v for group in pack.events.values() for v in group.values()]
    paths += [move.path for move in pack.moves.values()] + list(pack.turn.values())
    for path in paths:
        rel = path.removeprefix("/sd/apps/renamed_pet/")
        assert (APP / rel).is_file(), path
for category in manifest.categories.values():
    for name in category.files.values():
        assert (APP / "assets/skins/pc2005/normal" / name).is_file(), name
print("PASS: migration, 114 actions, renamed paths, speed fallback, no duplicate movements")

main = (APP / "main.lua").read_text(encoding="utf-8")
prefix = main.split("local config =")[0]
lua.execute('app={current=function() return {id="renamed_pet"} end}')
directory, slug = lua.execute(prefix + "\nreturn APP_DIR, APP_SLUG")
assert directory == "/sd/apps/renamed_pet" and slug == "renamed_pet"
controller_code = main.split("  local PAD_SELECT, PAD_HOME")[1].split("\nfunction APP.stop")[0]
controller_code = "local PAD_SELECT, PAD_HOME" + controller_code
controller_code = controller_code.rsplit("\nend", 1)[0]
for buttons, connected, expected in [(4096, True, 1), (32768, True, 1), (1, True, 0), (4096, False, 0)]:
    lua.execute("""
      exits=0; callback=nil
      APP={running=true,controller_buttons=0,stop=function() APP.running=false end}
      app={exit=function() exits=exits+1 end}
      tmr={ALARM_AUTO=1,create=function() return {alarm=function(_,_,_,fn) callback=fn end} end}
    """)
    lua.globals().test_buttons = buttons
    lua.globals().test_connected = connected
    lua.execute("controller={state=function() return {buttons=test_buttons,connected=test_connected} end}")
    lua.execute(controller_code)
    lua.execute("callback(); callback()")
    assert lua.globals().exits == expected
print("PASS: SELECT/HOME exit once, other buttons and disconnected controller ignored")

html = (APP / "info.html").read_text(encoding="utf-8")
encoded = re.search(r'src="data:image/png;base64,([^"]+)"', html).group(1)
assert base64.b64decode(encoded) == (APP / "main.png").read_bytes()
assert not re.search(r'<(?:script|img)[^>]+(?:src)="https?://', html)
assert "1.5.1" in html and "version = 1.5.1" in (APP / "app.info").read_text(encoding="utf-8")
js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
node_test = """
const vm=require('node:vm'), assert=require('node:assert/strict');
const elements={}; const document={documentElement:{},title:'',
getElementById(id){return elements[id] ||= {setAttribute(k,v){this[k]=v}}}};
const script=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
vm.runInNewContext(script,{document});
assert.equal(document.documentElement.lang,'zh-CN');
assert.equal(elements.lang.textContent,'EN');
elements.lang.onclick();
assert.equal(document.documentElement.lang,'en');
assert.equal(elements.lang.textContent,'中文');
assert.equal(elements.icon.alt,'HoloPet app icon');
elements.lang.onclick(); assert.equal(document.documentElement.lang,'zh-CN');
"""
import json
subprocess.run(["node", "-e", node_test], input=json.dumps(js), text=True, check=True)
web = (APP / "web.lua").read_text(encoding="utf-8")
assert 'option value="slow"' not in web and 'option value="fast"' not in web
assert "launch?id=dsh_fish" not in web
print("PASS: embedded original icon, bilingual page, version and WebUI options")
lua.execute("routes={}; httpd={GET=1,start=function() end,dynamic=function(_,path,fn) routes[path]=fn; return true end}")
web_module = lua.execute(web)
for language in ["zh-CN", "en"]:
    instance = web_module.new(lua.table_from({"language": language, "route_base": "/renamed_pet"}))
    instance.start(instance)
    rendered = lua.globals().routes["/renamed_pet/"]().body
    assert 'const API="/renamed_pet/api"' in rendered
    for script in re.findall(r"<script>(.*?)</script>", rendered, re.S):
        subprocess.run(["node", "--check"], input=script, text=True, encoding="utf-8", check=True)
print("PASS: generated WebUI JavaScript compiles in both languages with renamed route")
archive = ROOT / "dist/dsh_fish-1.5.1.zip"
if archive.exists():
    import zipfile
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names = set(z.namelist())
        for path in APP.rglob("*"):
            if path.is_file():
                name = "dsh_fish/" + path.relative_to(APP).as_posix()
                assert z.read(name) == path.read_bytes(), name
        assert "dsh_fish/LICENSE" in names and "dsh_fish/CREDITS.md" in names
        assert not any("/whale/" in name or "/fast/" in name or "/slow/" in name for name in names)
    print("PASS: ZIP integrity, packaged bytes and licensing notices")
files = list(p for p in APP.rglob("*") if p.is_file())
print(f"Package: {len(files)} files, {sum(p.stat().st_size for p in files)} bytes")
