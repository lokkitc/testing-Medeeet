from .models import Cart, CartItem


def cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    cart_items = cart.items.all()
    cart_total = cart.get_total_price()
    cart_count = sum(item.quantity for item in cart_items)
    
    return {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    }
