fetch('/payments/config/')
	.then((result) => {
		return result.json();
	})
	.then((data) => {
		// Initialize Stripe.js
		const stripe = Stripe(data.publicKey);
		// Event handler
		// Get Checkout Session ID
		fetch('/payments/' + structure_id + '/create-checkout-session/')
			.then((result) => {
				return result.json();
			})
			.then((data) => {
				// Redirect to Stripe Checkout
				return stripe.redirectToCheckout({ sessionId: data.sessionId });
			})
			.then((res) => {});
	});
