import py_compile, sys
files = [
    "decision_engine.py",
    "ai/chat_engine.py",
    "data_loader.py",
    "pages/8_\U0001f9e0_AI_Agronomist.py",
    "Home.py",
]
ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"  OK  {f}")
    except py_compile.PyCompileError as e:
        print(f"  FAIL {f}: {e}")
        ok = False
print("\nAll syntax OK" if ok else "\nSyntax ERRORS found above")
sys.exit(0 if ok else 1)
