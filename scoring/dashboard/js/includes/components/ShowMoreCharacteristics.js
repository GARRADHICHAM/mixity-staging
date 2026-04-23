import React from 'react';
import AssessIndicators from '../../EvaluationIndicator';

class ShowMoreCharacteristics extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			showCollaboratorsIndicators: false,
		};
	}

	toggleIndicators = () => {
		const newValue = !this.state.showCollaboratorsIndicators;
		this.setState({ showCollaboratorsIndicators: newValue });
		this.props.updateParentState('showCollaboratorsIndicators', newValue);
	};

	render() {
		const { isHumanPage, HumanCollaboratorInfoLoaded, CollaboratorsIndicators } = this.props;
		const { showCollaboratorsIndicators } = this.state;

		return (
			HumanCollaboratorInfoLoaded &&
			CollaboratorsIndicators && (
				<React.Fragment>
					<div className="card p-3 mb-3">
						<div className="d-flex justify-content-between align-items-middle" style={{ cursor: 'pointer' }} onClick={this.toggleIndicators}>
							<h3 className="mxt--normal-bold mb-0 me-2">
								{showCollaboratorsIndicators ? gettext('Afficher moins de caractéristiques') : gettext('Afficher plus de caractéristiques')}
							</h3>
							<img
								style={{
									width: '24px',
									transition: 'transform 0.3s',
									transform: showCollaboratorsIndicators ? 'rotate(180deg)' : 'rotate(0deg)',
								}}
								src={'/static/icon/chevron-dropdown.svg'}
								alt="toggle"
							/>
						</div>
						{showCollaboratorsIndicators && (
							<div className="d-flex justify-content-center flex-wrap w-100 p-0 mt-5" style={{ gap: '2rem' }}>
								{Array.isArray(CollaboratorsIndicators) && CollaboratorsIndicators.length > 2 ? (
									CollaboratorsIndicators.slice(2).map((indicator) => (
										<AssessIndicators
											key={indicator.title}
											category={'all'}
											json={indicator}
											index={indicator.id}
											isCriteria={true}
											isHuman={isHumanPage}
										/>
									))
								) : (
									<p>{gettext('Aucune caractéristique supplémentaire disponible.')}</p>
								)}
							</div>
						)}
					</div>
				</React.Fragment>
			)
		);
	}
}

export default ShowMoreCharacteristics;
