"""Application layer: use cases and the ports they depend on.

Each use case orchestrates the domain, enforces permissions, and owns its
transaction boundary. Ports (in ``application.ports``) are interfaces implemented
by adapters, so the core never imports a framework or a database driver.
"""
