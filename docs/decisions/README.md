# Architecture Decision Records

Short records of non-obvious decisions: the context, the decision, its
consequences, and the alternatives that were rejected. Each is immutable once
accepted; a later decision that reverses an earlier one is a new record.

Format is lightweight ([MADR](https://adr.github.io/madr/)-style).

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-two-process-architecture.md) | Two-process split: in-editor listener + external MCP server | Accepted (inherited from upstream) |
| [0002](0002-synchronous-scenecapture-screenshot.md) | Synchronous `SceneCapture2D` for viewport capture | Accepted |
| [0003](0003-dependency-injection-over-mocking-the-editor.md) | Dependency injection + stub `unreal` over mocking the editor | Accepted |
