import razorpay

# Initialize Razorpay client
# client = razorpay.Client(auth=("rzp_test_2hY8PR8G5rKybf", "E8w1YuPcAesivzTuSY5Y87qF"))
client = razorpay.Client(auth=("rzp_live_8kQ21NWsMXOu2S", "Q6rWc0EoKLmODmLKzAvKvz2S"))


class PaymentModel():

    def handle_payment(amount):
        payment_currency = 'INR'
        try:
            order = client.order.create({
                'amount': amount,
                'currency': payment_currency,
                'payment_capture': '1'
            })
            return order
        except Exception as e:
            return str(e)

    def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)
            return True
        except Exception:
            return False
