import React, { useState, useEffect } from 'react';

export default function DisplayProfile() {
	const [profile, setProfile] = useState(null);
	const [color, setColor] = useState("#8888E2");
	const [width, setWidth] = useState(0);
	const [completion, setCompletion] = useState("");

	const getProfile = async () => {
		let entity = window.location.pathname.split('/').filter(Boolean)[0];
		let product = window.location.pathname.split('/').filter(Boolean)[1];
		fetch(`/api/${entity}/${product}/survey/collaborator-info/`)
			.then((response) => {
				return response.json();
			})
			.then((data) => {
				setProfile(data[0].profile);
				var index = parseInt(data[0].profile.name[data[0].profile.name.length - 1]) - 1;
				var colors = ["#8888E2", "#0099FF", "#47D4FF", "#18FFC3"];
				var completions = ["Vous commencez votre parcours", "Vous êtes sur la bonne voie", "Vous touchez au but", "Vous avez terminé votre parcours"]
				var widths = [30, 60, 90, 100]

				if (index >= 0 && index <= 3) {
					setColor(colors[index]);
					setWidth(widths[index]);
					setCompletion(completions[index])
				}
			});
	};

	useEffect(() => {
		getProfile();
	}, []);

	if (!profile) {
		return <div>Chargement du profil...</div>;
	}

	return (
		<div className="d-flex flex-column" style={{ maxWidth: '50%' }}>
			<div className="d-flex flex-column flex-grow-1">
				<h1 className="mxt--large-bold mb-3">{gettext('Votre avancée')}</h1>
				<div className="card-profile-progress row p-3 flex-grow-1">
					<div className="my-3">
						<div>
							<h2 className="mxt--large-bold">{gettext(completion)}</h2>
						</div>
						<div
							className="w-100 progress-bar my-3 p-0"
							style={{
								height: '10px',
								backgroundColor: '#E6E8EC',
								borderRadius: '5px',
							}}
						>
							<div
								className="progress-bar-inner m-0"
								style={{
									width: `${width}%`,
									height: '10px',
									backgroundColor: color,
									borderRadius: '5px',
								}}
							></div>
						</div>
					</div>
					<div className="d-flex flex-column justify-content-start gap-3 mb-3">
						<p className="fw-medium mb-0">{gettext(profile.strenght)}</p>
						<p className="fw-medium mb-0">{gettext(profile.improvement)}</p>
						<p className="fw-medium mb-0">
							{gettext('Vos forces pour le futur : ')}
							<span className="txt_line content-strong"> {gettext(profile.type)}</span>
						</p>
					</div>
					{/* TODO : Création composant bouton Télécharger vos résultats */}
					{/* <div>
						<a
							className="excel-dropdown header-dropdown-toggle mxt--small button border assess_white_btn p-0 px-1"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
							id="direct_download_button"
						>
							<i className="bi bi-cloud-download"></i>
							{gettext('Télécharger vos résultats')}&nbsp;&nbsp;&nbsp;&nbsp;
						</a>
						<ul className="dropdown-menu">
							{this.props.languages.map((language) => {
								if (this.props.enabled_lang.includes(language)) {
									return (
										<li key={language.code}>
											<a
												style={{ cursor: 'pointer' }}
												className="dropdown-item"
												onClick={() => this.download_diag_human_sheet(language.code)}
											>
												<span className={`icon-flag-${language.code}`}></span>
												{language.label}({language.code})
											</a>
										</li>
									);
								}
								return null;
							})}
						</ul>
					</div> */}
				</div>
			</div>
		</div>
	);
}
