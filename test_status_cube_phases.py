import sys, json
sys.path.insert(0, 'src')
from convergence_io_engine import ConvergenceLoop

loop = ConvergenceLoop()
result = loop.run()

for p in result.get('phases', []):
    if p['phase'] in [12, 13, 14, 15]:
        print("Phase {} ({}): {} | issues: {}".format(
            p['phase'], p['name'], p['status'], len(p.get('issues_found', []))
        ))

print('convergence_score:', result.get('convergence_score'))
print('promotion_ready:', result.get('promotion_ready'))
