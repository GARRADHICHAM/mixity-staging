import React from 'react';

/*
 * Indicateur de chargement des pages : anneau animé, libellé qui respire et barre de progression.
 *
 * `message` est le texte d'état de la page (state.placeholder). Tant qu'il vaut « Chargement » (ou qu'il est
 * vide) on affiche l'animation ; si la page y met un message d'erreur, on l'affiche tel quel, sans animation.
 * Les styles sont inclus ici pour ne dépendre d'aucune feuille de style externe.
 */
const STYLES = `
@keyframes mx-loading-spin { to { transform: rotate(360deg); } }
@keyframes mx-loading-breathe { 0%, 100% { opacity: .45; } 50% { opacity: 1; } }
@keyframes mx-loading-slide { 0% { transform: translateX(-110%); } 100% { transform: translateX(260%); } }

.mx-loading {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 18px;
	width: 100%;
	min-height: 60vh;
	padding: 32px 16px;
	text-align: center;
}
.mx-loading__ring {
	width: 52px;
	height: 52px;
	border-radius: 50%;
	border: 4px solid rgba(136, 136, 226, 0.22);
	border-top-color: #8888e2;
	animation: mx-loading-spin 0.9s linear infinite;
}
.mx-loading__label {
	margin: 0;
	font-size: 1rem;
	font-weight: 600;
	letter-spacing: 0.02em;
	color: #181b3d;
	animation: mx-loading-breathe 1.6s ease-in-out infinite;
}
.mx-loading__track {
	position: relative;
	overflow: hidden;
	width: 160px;
	height: 4px;
	border-radius: 2px;
	background: rgba(136, 136, 226, 0.18);
}
.mx-loading__track::after {
	content: '';
	position: absolute;
	top: 0;
	bottom: 0;
	left: 0;
	width: 40%;
	border-radius: 2px;
	background: #8888e2;
	animation: mx-loading-slide 1.4s ease-in-out infinite;
}
.mx-loading--error .mx-loading__label { animation: none; opacity: 1; font-weight: 500; }
.mx-loading__icon {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 44px;
	height: 44px;
	border-radius: 50%;
	font-size: 1.5rem;
	font-weight: 700;
	color: #b3261e;
	background: rgba(179, 38, 30, 0.1);
}
@media (prefers-reduced-motion: reduce) {
	.mx-loading__ring { animation-duration: 3s; }
	.mx-loading__label { animation: none; opacity: 1; }
	.mx-loading__track::after { animation: none; width: 100%; opacity: 0.5; }
}
`;

const Loading = ({ message }) => {
	const isLoading = !message || message === gettext('Chargement');
	return (
		<div className={'mx-loading' + (isLoading ? '' : ' mx-loading--error')} role={isLoading ? 'status' : 'alert'} aria-live="polite">
			<style>{STYLES}</style>
			{isLoading ? (
				<>
					<div className="mx-loading__ring" aria-hidden="true" />
					<p className="mx-loading__label">{gettext('Chargement')}…</p>
					<div className="mx-loading__track" aria-hidden="true" />
				</>
			) : (
				<>
					<div className="mx-loading__icon" aria-hidden="true">
						!
					</div>
					<p className="mx-loading__label">{message}</p>
				</>
			)}
		</div>
	);
};

export default Loading;
