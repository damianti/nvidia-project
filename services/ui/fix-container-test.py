import re

with open('app/__tests__/services/containerService.test.ts', 'r') as f:
    content = f.read()

# Fix handlers without req, res, ctx parameters
content = re.sub(
    r"rest\.(get|post|put|delete)\(([^,]+),\s*\(\)\s*=>\s*\{",
    r"rest.\1(\2, (req, res, ctx) => {",
    content
)

content = re.sub(
    r"rest\.(get|post|put|delete)\(([^,]+),\s*async\s*\(\)\s*=>\s*\{",
    r"rest.\1(\2, async (req, res, ctx) => {",
    content
)

# Fix return res(ctx.json(..., { status: X })) to res(ctx.status(X), ctx.json(...))
content = re.sub(
    r"return res\(ctx\.json\(\s*(\{[^}]+\})\s*,\s*\{\s*status:\s*(\d+)\s*\}\s*\)",
    r"return res(\n            ctx.status(\2),\n            ctx.json(\1)",
    content
)

with open('app/__tests__/services/containerService.test.ts', 'w') as f:
    f.write(content)

print("Fixed containerService.test.ts")
