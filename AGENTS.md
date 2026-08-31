# Repository Guidelines

## Scope

- Keep this repository limited to Saint Nerona ComfyUI nodes.
- Prefer small, independent nodes over shared abstractions until logic is genuinely reused.
- Preserve existing node IDs, input names, output order, and workflow compatibility.

## ComfyUI Conventions

- Register nodes through `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.
- Define `INPUT_TYPES`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, and `CATEGORY` on every node.
- Treat `IMAGE` tensors as `[batch, height, width, channels]`.
- Keep display names under the `Saint Nerona` namespace and categories under `Saint Nerona/...`.

## Dependencies

- Use the Python standard library when possible.
- Add a dependency to both `requirements.txt` and `pyproject.toml` only when it is required at runtime.
- Do not add network requests, telemetry, analytics, or background downloads.

## Validation

- Add or update focused tests for calculation logic.
- Run `python -m unittest discover -s tests` before finishing changes.
- Keep `README.md` and `node_list.json` synchronized with registered nodes.
