from sqlalchemy.orm import Session
from . import models, schemas

def get_instance(db: Session, instance_id: int):
    return db.query(models.WarpInstance).filter(models.WarpInstance.id == instance_id).first()

def get_instance_by_name(db: Session, name: str):
    return db.query(models.WarpInstance).filter(models.WarpInstance.name == name).first()

def get_instances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WarpInstance).offset(skip).limit(limit).all()

def create_instance(db: Session, instance: schemas.WarpInstanceCreate):
    db_instance = models.WarpInstance(**instance.dict())
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

def update_instance(db: Session, db_instance: models.WarpInstance, instance_in: schemas.WarpInstanceUpdate):
    update_data = instance_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_instance, key, value)
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

def delete_instance(db: Session, instance_id: int):
    db_instance = db.query(models.WarpInstance).filter(models.WarpInstance.id == instance_id).first()
    if db_instance:
        db.delete(db_instance)
        db.commit()
    return db_instance