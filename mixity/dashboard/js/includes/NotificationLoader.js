import React, { Component } from 'react';

class NotificationLoader extends Component {
	constructor(props) {
		super(props);
		this.state = {
			showToast: false,
			toastMessage: '',
			toastClass: '',
			animationToastClass: '',
			toastLogo: '',
			isAnimating: false,
		};
	}

	componentDidUpdate(prevProps) {
		if (this.props.is_active && this.props.is_active !== prevProps.is_active) {
			this.handleAPIRequest();
		}
	}

	handleAPIRequest = async () => {
		if (this.state.isAnimating) {
			return;
		}

		try {
			this.setState({ isAnimating: true });
			await this.apiRequest();
			this.props.onRequestComplete(false);
		} catch (error) {
			console.error("Erreur lors de l'appel à apiRequest :", error);
		} finally {
			this.setState({ isAnimating: false });
		}
	};

	apiRequest = async () => {
		const { apiUrl, method, formData } = this.props;
		const requestOptions = {
			credentials: 'include',
			method: method,
			headers: { 'X-CSRFToken': csrftoken },
			body: formData || null, // Utiliser formData si fourni, sinon null
		};

		if (!formData) {
			requestOptions.headers['Content-Type'] = 'application/json;charset=utf-8';
		}

		this.showToastWithAnimation(gettext('Chargement en cours ...'));
		this.setState({
			toastClass: 'api_request_loading',
			toastLogo: '/static/img/icon_loading.svg',
		});

		try {
			const response = await fetch(apiUrl, requestOptions);
			const data = await response.json();

			if (response.ok) {
				this.setState({
					toastClass: 'api_request_success',
					toastLogo: '/static/img/icon_success.svg',
				});
				this.showToastWithAnimation(gettext(data.message));
			} else {
				this.setState({
					toastClass: 'api_request_fail',
					toastLogo: '/static/img/icon_fail.svg',
				});
				this.showToastWithAnimation(gettext(data.message) || gettext('Une erreur est survenue.'));
			}
		} catch (error) {
			this.setState({
				toastClass: 'api_request_fail',
				toastLogo: '/static/img/icon_fail.svg',
			});
			this.showToastWithAnimation(gettext('Une erreur interne est survenue, merci de réessayer plus tard.'));
		}
	};

	showToastWithAnimation = (message) => {
		this.setState({
			showToast: true,
			toastMessage: message,
			animationToastClass: 'slide-in',
		});

		setTimeout(() => {
			this.setState(
				{
					animationToastClass: 'slide-out',
				},
				() => {
					setTimeout(() => {
						this.setState({ showToast: false });
					}, 500);
				},
			);
		}, 5000);
	};

	render() {
		const { showToast, toastMessage, animationToastClass, toastClass, toastLogo } = this.state;

		return (
			showToast && (
				<div className="d-flex justify-content-center">
					<div className={`dashboard api_request d-flex flex-start align-items-center ${toastClass} ${animationToastClass}`}>
						<img
							src={toastLogo}
							alt=""
							style={{
								height: '2vh',
								width: 'auto',
								marginRight: '2%',
								marginLeft: '2%',
							}}
						/>
						<p style={{ margin: '0px', padding: '0.5rem 2rem 0.5rem 2rem' }}>{toastMessage}</p>
					</div>
				</div>
			)
		);
	}
}

export default NotificationLoader;
