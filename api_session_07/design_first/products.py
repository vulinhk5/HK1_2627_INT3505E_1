from models import db, Product

def list_products():
    rows = db.session.execute(db.select(Product)).scalars().all()
    return [p.to_dict() for p in rows], 200

def create_product(body):
    p = Product(**body)
    db.session.add(p)
    db.session.commit()
    return p.to_dict(), 201

def get_product(id):
    p = db.get_or_404(Product, id)
    return p.to_dict(), 200