import React, { Component } from 'react';

class AssessSheetDirectDownload extends Component {
	constructor(props) {
		super();
	}

	async download_human_pdf(language_code) {
		const directdownloadbutton = document.getElementById('direct_download_button_pdf');
		const directdownloadelement = document.getElementById('direct_download_element');
		const directdownloadmsg = document.getElementById('direct_download_msg');
		let cookies = document.cookie.split(';');

		directdownloadbutton.setAttribute('aria-expanded', 'false');
		directdownloadbutton.style.opacity = '0.5';
		directdownloadbutton.style.pointerEvents = 'none';
		directdownloadelement.style.display = 'block';
		directdownloadmsg.textContent = gettext('chargement en cours ...');
		await fetch(`/scoring/evaluation/${this.props.evaluation.pk}/react_human_filtered_pdf/`, {
			credentials: 'include',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json;charset=utf-8',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({ language_code: language_code, filter: this.props.defaultFormInputs, cookies: cookies }),
		})
			.then((response) => response.json())
			.then((data) => {
				directdownloadelement.style.display = 'block';
				if (data.code == 200) {
					directdownloadelement.style.backgroundColor = 'rgb(50, 255, 50, 50)';
					directdownloadmsg.textContent = data.message;
				} else if (data.code == 404) {
					directdownloadelement.style.backgroundColor = 'rgb(255, 15, 0, 50)';
					directdownloadmsg.textContent = data.message;
				} else {
					directdownloadelement.style.backgroundColor = 'rgb(255, 127, 0, 50)';
					directdownloadmsg.textContent = gettext('une erreur interne est survenue merci de réessayer plus tard');
				}
				setTimeout(() => {
					directdownloadelement.style.backgroundColor = 'rgb(255, 255, 255, 0)';
					directdownloadelement.style.display = 'none';
					directdownloadmsg.textContent = '';
				}, 5000);
			})
			.catch((error) => {
				directdownloadelement.style.backgroundColor = 'rgb(255, 127, 0, 50)';
				directdownloadmsg.textContent = gettext('une erreur interne est survenue merci de réessayer plus tard');
			});
		setTimeout(async () => {
			directdownloadelement.style.backgroundColor = 'rgb(255, 255, 255, 0)';
			directdownloadelement.style.display = 'none';
			directdownloadmsg.textContent = '';
			directdownloadbutton.style = { opacity: '1', cursor: 'pointer' };
		}, 5000);
	}

	render() {
		return (
			<>
				<meta id="human_pdf_pk" data-pk={this.props.evaluation.pk} />

				<div className="nav-item dropdown">
					<>
						<a
							className="pdf-dropdown mxt--small button border assess_white_btn p-0 px-1"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
							id="direct_download_button_pdf"
						>
							<i className="bi bi-cloud-download"></i>
							{this.props.evaluation.is_validated_by_user ? `${gettext('Pdf')}` : `${gettext('Pdf en cours')}`}&nbsp;&nbsp;&nbsp;&nbsp;
						</a>
					</>
					<ul className="dropdown-menu">
						{this.props.languages.map((language) => {
							if (this.props.enabled_lang.includes(language)) {
								return (
									<li key={language.code}>
										<a style={{ cursor: 'pointer' }} className="dropdown-item" onClick={() => this.download_human_pdf(language.code)}>
											<span className={`icon-flag-${language.code}`}></span>
											{language.label}({language.code})
										</a>
									</li>
								);
							}
							return null;
						})}
					</ul>
				</div>
			</>
		);
	}
}

export default AssessSheetDirectDownload;
