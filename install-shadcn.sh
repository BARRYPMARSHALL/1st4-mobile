#!/bin/bash
cd /home/free33/dev/1st4-mobile/frontend
components="card input label dialog table tabs badge separator dropdown-menu avatar progress select textarea checkbox scroll-area sheet tooltip separator"
for c in $components; do
  npx shadcn@latest add "$c" -y 2>/dev/null
done
echo "Done"
