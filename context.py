# app/context.py
from dataclasses import dataclass

@dataclass
class AppContext:
    db: any = None       # fachada / db_instance
    conn: any = None     # conexión Oracle
    user: any = None     # objeto usuario

def get_ctx(page) -> AppContext:
    return page.session.get("ctx") or AppContext()

def set_ctx(page, ctx: AppContext):
    page.session.set("ctx", ctx)