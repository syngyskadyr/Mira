import importlib, sys

modules = [
    "backend.database",
    "backend.services",
    "data.tasks",
    "bot.handlers",
    "bot.keyboards",
]

errors = []
for m in modules:
    try:
        importlib.import_module(m)
        print("imported", m)
    except Exception as e:
        print("FAILED", m, e)
        errors.append((m, str(e)))

if errors:
    print("\nErrors detected:")
    for m, e in errors:
        print(m, e)
    sys.exit(1)

print("ALL OK")
