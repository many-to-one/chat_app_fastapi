from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, Depends, status

from models.users import User
from security.security import verify_password, get_tokens_pair

class OrmService:
    def __init__(self, db):
        self.db = db

    
    async def login(self, form):
        # print('--login--form--', form.username)
        result = await self.db.execute(select(User).filter(User.username == form.username))  # Await the query execution
        user = result.scalar_one_or_none() 
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

        if not verify_password(form.password, user.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
        
        user.is_active = True
        await self.db.commit()
 
        return await get_tokens_pair(db=self.db, id=user.id)

    
    async def all(self, model, name):

        result = await self.db.execute(select(model))
        obj = result.scalars().all()

        if obj is None:
            raise HTTPException(status_code=404, detail=f"No {name}")
        
        return obj
    

    async def create(self, model, form):

        if isinstance(form, dict):
            obj_dict = form
        else:
            obj_dict = form.dict()

        obj = model(**obj_dict)

        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    

    async def get(self, id: int, model, name):

        result = await self.db.execute(select(model).filter(model.id == id))
        obj = result.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail=f"No {name}")
        
        return obj
    

    async def update(self, form, id, model, name):

        obj = await self.get(id=id, model=model, name=name)
    
        if not obj:
            raise HTTPException(status_code=404, detail=f"No such {name}")
        
        for field, value in form.dict().items():
            if value is not None:
                setattr(obj, field, value)

        await self.db.commit()  
        await self.db.refresh(obj)
        return obj
    

    async def delete(self, id: int, model, name):

        result = await self.db.execute(select(model).filter(model.id == id))
        obj = result.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail=f"No {name}")
        
        await self.db.delete(obj)
        await self.db.commit()
        await self.db.flush()
        
        return {
            "message": f"{name} deleted successfully!",
            "userMessage": f"Objekt {name} został usunięty!",
            }
    


    # async def delete_product(self, id: int):
    #     # Find and delete the associated CartItem first
    #     cart_item = await self.db.execute(
    #         select(CartItem).filter(CartItem.product_id == id)
    #     )
    #     cart_item = cart_item.scalar_one_or_none()

    #     if cart_item:
    #         await self.db.delete(cart_item)
    #         # No need to commit here; we'll commit everything at once later.

    #     # Now find and delete the Product
    #     product = await self.db.execute(
    #         select(Product).filter(Product.id == id)
    #     )
    #     product = product.scalar_one_or_none()

    #     if product:
    #         await self.db.delete(product)
    #         await self.db.commit()  # Commit all changes in one transaction
    #         return {"message": "Product and associated cart item(s) deleted successfully!"}
    #     else:
    #         # If the product doesn't exist, raise an error
    #         raise HTTPException(status_code=404, detail="Product not found")