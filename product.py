# This file is part of product_special_price module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.config import config as config_

__all__ = ['Template', 'Product']

STATES = {
    'readonly': ~Eval('active', True),
    }
DEPENDS = ['active']
DIGITS = config_.getint('product', 'price_decimal', default=4)


class Template:
    __metaclass__ = PoolMeta
    __name__ = 'product.template'
    special_price = fields.Property(fields.Numeric('Special Price',
        states=STATES, digits=(16, DIGITS), depends=DEPENDS))
    special_price_from = fields.Date('Special Price From')
    special_price_to = fields.Date('Special Price To')


class Product:
    __metaclass__ = PoolMeta
    __name__ = 'product.product'

    @classmethod
    def get_sale_price(cls, products, quantity=0):
        pool = Pool()
        Date = pool.get('ir.date')
        User = pool.get('res.user')
        Uom = pool.get('product.uom')

        prices = super(Product, cls).get_sale_price(products, quantity)

        if Transaction().context.get('without_special_price'):
            return prices

        today = Date.today()
        user = User(Transaction().user)
        if user.shop and user.shop.special_price:
            for product in products:
                if (product.special_price_from and
                        today < product.special_price_from):
                    continue
                if (product.special_price_to and
                        today > product.special_price_to):
                    continue
                special_price = 0.0
                if user.shop.type_special_price == 'pricelist':
                    price_list = user.shop.special_pricelist
                    customer = Transaction().context.get('customer', None)
                    uom_id = Transaction().context.get('uom', None)
                    if uom_id:
                        uom = Uom(uom_id)
                    else:
                        uom = product.default_uom
                    special_price = price_list.compute(customer, product,
                        prices[product.id], quantity, uom)
                else:
                    special_price = product.special_price

                if special_price != 0.0 and special_price != None and \
                        special_price < prices[product.id]:
                    prices[product.id] = special_price
        return prices
