"""Shared kernel for the customer portal.

Domain code may import ``portal_common.identity`` only. Token signing and the
FastAPI dependency live in adapter modules and must not be imported by domain
packages.
"""
