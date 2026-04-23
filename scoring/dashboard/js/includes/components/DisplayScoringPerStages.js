import AssessSubCategoryScore from '../../includes/AssessSubCategoryScore';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';

import React, { useState, useEffect } from 'react';
import { Card, Modal } from 'react-bootstrap';
import { getColors } from '../ColorData';

export default function DisplayScoringPerStages(props) {
	// correpond aux subcategories
	const [scoringPerStages, setScoringPerStages] = useState({});
	const [benchmarkActive, setBenchmarkActive] = useState(false);

	const [showModal, setShowModal] = useState(false);

	useEffect(() => {
		setScoringPerStages(props.data.subcategories);
		setBenchmarkActive(props.data.benchmark);
	}, [props.data.subcategories, props.data.benchmark]);

	if (!scoringPerStages) {
		return <div></div>;
	}
	return (
		<div className="card d-flex flex-column w-100">
			<div className="d-flex align-items-center">
				<div className="d-flex align-items-center w-25">
					<h3 className="mxt--normal-bold m-0">{gettext('Score par phase')}</h3>
					<div className="ms-3 custom_tooltip" onClick={() => setShowModal(!showModal)}>
						?
					</div>
				</div>
				{benchmarkActive && (
					<div className="d-flex row-flex justify-content-end align-items-center w-75">
						<div className="d-flex row-flex">
							<div style={{ width: '1.5em', marginRight: '.5rem' }}>
								<CircularProgressbar value={10} background styles={buildStyles({ backgroundColor: '#8888E2' })} />
							</div>
							<span className="fw-bold"> Vous</span>
						</div>
						<div className="d-flex row-flex">
							<div style={{ width: '1.5em', marginRight: '.5rem', marginLeft: '1rem' }}>
								<CircularProgressbar value={10} background styles={buildStyles({ backgroundColor: getColors('meanscore_sector', [1]) })} />
							</div>
							<span className="fw-bold"> Score moyen dans le secteur</span>
						</div>
						<div className="d-flex row-flex">
							<div style={{ width: '1.5em', marginRight: '.5rem', marginLeft: '1rem' }}>
								<CircularProgressbar value={10} background styles={buildStyles({ backgroundColor: getColors('meanscore_global', [1]) })} />
							</div>
							<span className="fw-bold"> Score moyen global</span>
						</div>
					</div>
				)}
			</div>
			<div className="mt-4">
				<p className="p-0 m-0">
					{gettext(
						"L'analyse des phases consiste à structurer l'évaluation en étapes clés correspondant aux différentes dimensions des compétences inclusives. Chaque phase est associée à des notions spécifiques et mesurées par des questions précises du référentiel Mixity qui détermine l’empreinte. C’est une analyse complémentaire et ne reflète pas le score global de l’empreinte.",
					)}
				</p>
			</div>
			<div className="d-flex flex-wrap mt-5 justify-content-around" style={{ gap: '2rem' }}>
				{Object.values(scoringPerStages).map((subcat, key) => (
					<div
						className="d-block m-2"
						key={key}
						style={{
							flexGrow: 1,
							minWidth: '10%',
							maxWidth: '15%',
						}}
					>
						<div className="d-flex justify-content-around align-items-center flex-column p-2">
							<AssessSubCategoryScore
								key={key}
								subCatPercent={Math.round(subcat.score)}
								subCatSectorPercent={Math.round(subcat.sector_score)}
								subCatGlobalPercent={Math.round(subcat.global_score)}
								benchmarkActive={benchmarkActive}
								subCatName={gettext(subcat.name)}
								subCatColor={'#8888E2'}
							/>
						</div>
					</div>
				))}
			</div>
			<Modal
				show={showModal}
				onHide={() => setShowModal(false)}
				aria-labelledby="contained-modal-title-vcenter"
				size={'lg'}
				style={{ zIndex: '1050' }}
				className="criteria_modal m-0 p-0"
				centered
			>
				<Modal.Header closeButton className="align-items-start" style={{ border: 'none' }}>
					<div className="w-100">
						<h2>{gettext('Méthodologie : évaluation des phases Scan Recruit')}</h2>
					</div>
				</Modal.Header>
				<Modal.Body>
					<div className="w-100">
						<p>
							{gettext(
								"Avertissement - la notation relative à l'évaluation des compétences en fonction des phases de recrutement ne reflète pas le score global de l’empreinte Mixity. C'est une analyse complémentaire, avec son propre système de notation, qui permet d’évaluer les niveaux de maturité des recruteurs sur les différentes phases du process de recrutement.",
							)}
						</p>
						<ol>
							<li className="mt-5">
								<h3>
									<b>{gettext('Préparation : Planifier un recrutement inclusif')}</b>
								</h3>
							</li>
							<ul>
								<li>
									<p>
										<b>{gettext('Objectif : ')}</b>
										{gettext(
											'Vérifier que le recruteur maîtrise les bases nécessaires pour définir des besoins inclusifs et éviter les biais dès le début du processus.',
										)}
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Exemple de question :')}</b>
										<br />
										<i>{gettext('« Quelle est la définition d’un préjugé ? »')}</i>
										<ul className="pt-0">
											<li>{gettext('Réponse possible : « Ce sont des idées générales que nous portons sur un groupe », etc.')}</li>
										</ul>
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Analyse : ')}</b>
										{gettext(
											"Cette question évalue si le recruteur est capable d'identifier ses propres biais pour rédiger des description de poste neutres et inclusives.",
										)}
									</p>
								</li>
							</ul>
							<li className="mt-5">
								<h3>
									<b>{gettext('Sourcing : Diversifier les canaux de recherche')}</b>
								</h3>
							</li>
							<ul>
								<li>
									<p>
										<b>{gettext('Objectif : ')}</b>
										{gettext(
											'Tester la capacité à rechercher activement des candidats diversifiés et à utiliser des outils pour réduire les biais de sourcing.',
										)}
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Exemple de question :')}</b>
										<br />
										<i>
											{gettext(
												'« Une offre d’emploi avec de nombreuses compétences demandées permet de (une ou plusieurs réponses possibles) :',
											)}
										</i>
										<ul className="pt-0">
											<li>
												<i>
													{gettext(
														'S’assurer d’obtenir des candidats ou candidates motivés qui seront très engagés dans l’entreprise;',
													)}
												</i>
											</li>
											<li>
												<i>{gettext('S’assurer d’obtenir des candidats qualifiés qui ont les compétences requises;')}</i>
											</li>
											<li>
												<i>{gettext("S'assurer d’obtenir des candidats surqualifiés et donc plus performants;")}</i>
											</li>
											<li>
												<i>{gettext('Aucune de ces réponses. »')}</i>
											</li>
										</ul>
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Analyse : ')}</b>
										{gettext(
											"Cette question vérifie si le recruteur a conscience de l'impact de la rédaction d'une offre d'emploi sur le nombre de candidats qui vont postuler.",
										)}
									</p>
								</li>
							</ul>
							<li className="mt-5">
								<h3>
									<b>{gettext('Entretien : Conduire une évaluation objective et bienveillante')}</b>
								</h3>
							</li>
							<ul>
								<li>
									<p>
										<b>{gettext('Objectif : ')}</b>
										{gettext(
											'Évaluer les compétences pour mener un entretien structuré, écouter activement, et poser des questions neutres.',
										)}
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Exemple de question :')}</b>
										<br />
										<i>
											{gettext(
												'« Vous recevez un candidat avec des piercings au visage pour un poste directement en contact avec la clientèle. Votre collègue vous confie qu’elle a peur que cette personne donne une impression peu professionnelle aux clients : comment réagissez-vous ? »',
											)}
										</i>
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Analyse : ')}</b>
										{gettext(
											'Cela mesure la compréhension des risques juridiques et la capacité à éviter des pratiques discriminatoires pendant l’entretien.',
										)}
									</p>
								</li>
							</ul>
							<li className="mt-5">
								<h3>
									<b>{gettext('Sélection : Choicir objectivement le candidat')}</b>
								</h3>
							</li>
							<ul>
								<li>
									<p>
										<b>{gettext('Objectif : ')}</b>
										{gettext(
											'Tester la capacité à appliquer des critères objectifs et à utiliser des outils standardisés pour sélectionner un candidat.',
										)}
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Exemple de question :')}</b>
										<br />
										<i>
											{gettext(
												'« Entre deux personnes candidates avec les mêmes compétences, comment choisir la personne à recruter (une ou plusieurs réponses possibles) :',
											)}
										</i>
										<ul className="pt-0">
											<li>
												<i>{gettext("J'ajoute une étape pour décider (entretien, exercice...)")}</i>
											</li>
											<li>
												<i>{gettext('Je tire à pile ou face')}</i>
											</li>
											<li>
												<i>{gettext('Je demande un avis à des pairs')}</i>
											</li>
											<li>
												<i>{gettext('Je choisis le profil le plus affinitaire avec mes valeurs personnelles »')}</i>
											</li>
										</ul>
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Analyse : ')}</b>
										{gettext(
											'Cette question vérifie si le recruteur peut identifier et prévenir les discriminations indirectes lors de la décision finale.',
										)}
									</p>
								</li>
							</ul>
							<li className="mt-5">
								<h3>
									<b>{gettext('Onboarding : Intégrer le candidat dans une dynamique inclusive')}</b>
								</h3>
							</li>
							<ul>
								<li>
									<p>
										<b>{gettext('Objectif : ')}</b>
										{gettext('Évaluer la capacité à créer un environnement de travail accueillant et équitable pour le nouvel employé.')}
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Exemple de question :')}</b>
										<br />
										<i>
											{gettext(
												"« En phase d'onboarding d'une nouvelle collaboratrice, celle-ci vous mentionne qu'elle souhaite débuter une transition de genre : comment réagissez-vous ? »",
											)}
										</i>
									</p>
								</li>
								<li>
									<p>
										<b>{gettext('Analyse : ')}</b>
										{gettext(
											"Cela mesure la sensibilisation du recruteur à l’importance d’adapter les conditions de travail pour différents profils et aussi son niveau de connaissance de l'inclusion de ce profil dans l'entreprise.",
										)}
									</p>
								</li>
							</ul>
						</ol>
						<h3 className="mt-5">
							<b>{gettext('Synthèse : Une analyse progressive et ciblée')}</b>
						</h3>
						<p>{gettext('Chaque phase est conçue pour évaluer des dimensions spécifiques du processus de recrutement inclusif :')}</p>
						<ul>
							<li>
								<p>
									<b>{gettext('Préparation : ')}</b>
									{gettext('Connaissances fondamentales pour éviter les biais initiaux.')}
								</p>
							</li>
							<li>
								<p>
									<b>{gettext('Sourcing : ')}</b>
									{gettext('Diversification et conformité légale.')}
								</p>
							</li>
							<li>
								<p>
									<b>{gettext('Entretien : ')}</b>
									{gettext('Neutralité et écoute active.')}
								</p>
							</li>
							<li>
								<p>
									<b>{gettext('Sélection : ')}</b>
									{gettext('Objectivité et équité.')}
								</p>
							</li>
							<li>
								<p>
									<b>{gettext('Onboarding : ')}</b>
									{gettext('Intégration et soutien adaptés.')}
								</p>
							</li>
						</ul>
					</div>
				</Modal.Body>
			</Modal>
		</div>
	);
}
