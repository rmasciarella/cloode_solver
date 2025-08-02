#!/bin/bash

# Script to update imports in pages that use the refactored forms

echo "Updating form imports to use refactored components..."

# Update SkillForm imports
if grep -l "from '@/components/forms/SkillForm'" app/**/*.tsx 2>/dev/null; then
  echo "Updating SkillForm imports..."
  find app -name "*.tsx" -type f -exec sed -i '' \
    "s|from '@/components/forms/SkillForm'|from '@/components/forms/skills/SkillFormRefactored'|g" {} \;
fi

# Update MachineForm imports
if grep -l "from '@/components/forms/MachineForm'" app/**/*.tsx 2>/dev/null; then
  echo "Updating MachineForm imports..."
  find app -name "*.tsx" -type f -exec sed -i '' \
    "s|from '@/components/forms/MachineForm'|from '@/components/forms/machines/MachineFormRefactored'|g" {} \;
fi

# Update SetupTimeForm imports
if grep -l "from '@/components/forms/SetupTimeForm'" app/**/*.tsx 2>/dev/null; then
  echo "Updating SetupTimeForm imports..."
  find app -name "*.tsx" -type f -exec sed -i '' \
    "s|from '@/components/forms/SetupTimeForm'|from '@/components/forms/setup-times/SetupTimeFormRefactored'|g" {} \;
fi

echo "Import updates complete!"

# Optional: List all form imports to verify
echo -e "\nCurrent form imports:"
grep -r "from '@/components/forms/" app --include="*.tsx" | grep -E "(SkillForm|MachineForm|SetupTimeForm)" || echo "No old imports found"