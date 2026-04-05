import importlib
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_monster():
    print("--- [SYSTEM] HARVESTER INITIALIZED ---")

    acc = 32416190071
    base_dir = os.path.dirname(os.path.abspath(__file__))
    h_dir = os.path.join(base_dir, 'harvesters')

    files = [f[:-3] for f in os.listdir(h_dir) if f.endswith('.py') and f != '__init__.py']
    print(f"[*] Analyzing {len(files)} modules...")

    for name in sorted(files):
        try:
            module = importlib.import_module(f"harvesters.{name}")
            print(f"\n[EXEC] Running: {name}")

            val = module.harvest()

            if val > 0:
                old_acc = acc
                acc = (acc ^ val) + val
                print(f"  + Added: {val}")
                print(f"  = Seed:  {acc}")
            else:
                print(f"  - No data provided by {name}")

        except Exception as e:
            print(f"  ! CRITICAL ERROR in {name}: {type(e).__name__}")
            print(f"    {str(e)}")

    print("\n" + "="*30)
    print(f"FINAL SEED: {acc}")
    print("="*30)

if __name__ == "__main__":
    run_monster()
