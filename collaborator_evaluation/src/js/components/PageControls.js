import React from 'react';
import './PageControls.css';

export default function PageControls(props) {
	const nextButtonStyle = !props.unlockNextButton
		? {
				backgroundColor: 'lightgray',
				cursor: 'not-allowed',
			}
		: {};
	return (
		<div className="page-controls">
			<div />
			<div className="page-control-buttons " style={{ marginLeft: '-51%', width: '151%', marginTop: '-117px' }}>
				{props.showPreviousButton ? (
					<div className="page-controls-button-container">
						<button className="button button--circle button-previous page-control-button" onClick={props.handlePreviousPageButtonClick}>
							{gettext('< Question précédente')}
						</button>
					</div>
				) : (
					<div />
				)}
				{props.displaySubmit ? (
					<div className="page-controls-button-container">
						<button
							className="button-next button button--circle button--secondary page-control-button"
							onClick={props.handleSubmit}
							style={nextButtonStyle}
						>
							{gettext('Valider et quitter le questionnaire')}
						</button>
					</div>
				) : (
					<div className="page-controls-button-container">
						<button
							style={nextButtonStyle}
							disabled={!props.unlockNextButton}
							className="button-next button button--circle button--secondary page-control-button"
							onClick={props.handleNextPageButtonClick}
						>
							{props.nextButtonLabel}
						</button>
					</div>
				)}
			</div>
		</div>
	);
}
