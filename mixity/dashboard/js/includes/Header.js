import React from 'react';

export default class Header extends React.Component {
	constructor(props) {
		super(props);
	}

	languageSelectorFunction(languageCode) {
		document.cookie = 'language_code=' + languageCode + '; path=/;';
		window.location.reload(true);
	}

	render() {
		return (
			<div>
				<a
					className="header-dropdown-toggle header-dropdown-toggle-lang mxt--small pe-5"
					href="#"
					role="button"
					data-bs-toggle="dropdown"
					aria-expanded="false"
				>
					<span className={`${'icon-flag-' + this.props.data.language_code}`}></span>
					{this.props.data.language_code}
				</a>
				<ul className="dropdown-menu">
					{this.props.data.languages
						.filter((lang) => this.props.data.enabled_website_languages.includes(lang.code) && lang.code != this.props.data.language_code)
						.map((language) => {
							return (
								<li key={language.code}>
									<button
										style={{ cursor: 'pointer' }}
										className="dropdown-item"
										onClick={(e) => this.languageSelectorFunction(language.code)}
									>
										<span className={`${'icon-flag-' + language.code}`}></span>
										{language.name} <span style={{ textTransform: 'uppercase' }}>({language.code})</span>
									</button>
								</li>
							);
						})}
				</ul>
				<a
					className="header-dropdown-toggle mxt--small pe-5"
					href="#"
					id="offcanvasNavbarDropdown"
					role="button"
					data-bs-toggle="dropdown"
					aria-expanded="false"
				>
					{gettext('Mon compte')}
				</a>
				<ul className="dropdown-menu">
					<li>
						<a className="dropdown-item" href={'/account/update_profile/'}>
							<div className="d-inline-block">{gettext('Mes informations')}</div>
						</a>
					</li>
					<li>
						<a className="dropdown-item" href={'/account/password-change/'}>
							<div className="d-inline-block">{gettext('Mes identifiants')}</div>
						</a>
					</li>
					<li>
						<a className="dropdown-item" href={'/user/logout/'}>
							<div className="d-inline-block">{gettext('Se déconnecter')}</div>
						</a>
					</li>
				</ul>
			</div>
		);
	}
}
