import React, { Component } from 'react';
import { getColors } from './ColorData';

export default class StrengthsAndWeaknesses extends Component {
	constructor(props) {
		super(props);
		this.state = {
			strengthsDetails: false,
			weaknessesDetails: false,
			aimsDetails: false,
		};
	}

	render() {
		return (
			<React.Fragment>
				<div className="card public_axe strenght_container" style={{ padding: '2rem', margin: '1rem', width: '47%', borderRadius: '25px' }}>
					<div className="points_title mb-3">
						<div className="d-flex align-items-center">
							<h2 className="txt_line title--h2">{gettext('Points forts')}</h2>
						</div>
					</div>

					{this.props.strengths.slice(0, this.state.strengthsDetails ? this.props.strengths.length : 3).map((strength, index) => {
						return (
							strength.description && (
								<div className="strenght_answer_container row mb-2 mx-2 mt-4">
									<div className="icon">
										<i className="bi bi-hand-thumbs-up align-self-center" style={{ color: getColors(strength.category, [1]) }}></i>
									</div>
									<div className="strenght_answer">
										<div className="mxt--h4">{strength.custom_title ? strength.custom_title : strength.subcategory}</div>
										<div className="mxt--small">{strength.description}</div>
									</div>
								</div>
							)
						);
					})}
					{this.props.strengths.length === 0 && this.props.CommentsLoaded && <div className="mb-3">{gettext('Aucun point fort')}</div>}
					{/*<div className="mb-3" style={{ display: this.props.CommentsLoaded ? 'none' : 'block' }}>*/}
					{/*	{gettext('Chargement')}*/}
					{/*</div>*/}

					{this.props.strengths.length > 3 && (
						<div
							className="d-flex justify-content-center"
							style={{ color: getColors(this.props.strengths[0].category, [1]), cursor: 'pointer' }}
							onClick={() => this.setState({ strengthsDetails: !this.state.strengthsDetails })}
						>
							<p className="m-0">
								{this.state.strengthsDetails ? (
									<>
										<strong>-</strong> {gettext('Masquer les détails')}
									</>
								) : (
									<>
										<strong>+</strong> {gettext('Plus de détails')}
									</>
								)}
							</p>
						</div>
					)}
				</div>

				<div className="card public_axe weakness_container" style={{ padding: '2rem', margin: '1rem', width: '47%', borderRadius: '25px' }}>
					<div className="points_title mb-3">
						<div className="d-flex align-items-center">
							<h2 className="txt_line title--h2">{gettext("Axes d'amélioration")}</h2>
						</div>
					</div>

					{this.props.weaknesses.slice(0, this.state.weaknessesDetails ? this.props.weaknesses.length : 3).map((weakness, index) => {
						return (
							weakness.description && (
								<div className="weakness_answer_container row mb-2 mx-2 mt-4">
									<div className="icon">
										<i className="bi bi-award align-self-center" style={{ color: getColors(weakness.category, [1]) }}></i>
									</div>
									<div className="weakness_answer">
										<div className="mxt--h4">{weakness.custom_title ? weakness.custom_title : weakness.subcategory}</div>
										<div className="mxt--small">{weakness.description}</div>
									</div>
								</div>
							)
						);
					})}
					{this.props.weaknesses.length === 0 && this.props.CommentsLoaded && <div className="mb-3">{gettext("Aucun axe d'amélioration")}</div>}
					{/*<div className="mb-3" style={{ display: this.props.CommentsLoaded ? 'none' : 'block' }}>*/}
					{/*	{gettext('Chargement')}*/}
					{/*</div>*/}

					{this.props.weaknesses.length > 3 && (
						<div
							className="d-flex justify-content-center"
							style={{ color: getColors(this.props.weaknesses[0].category, [1]), cursor: 'pointer' }}
							onClick={() => this.setState({ weaknessesDetails: !this.state.weaknessesDetails })}
						>
							<p className="m-0">
								{this.state.weaknessesDetails ? (
									<>
										<strong>-</strong> {gettext('Masquer les détails')}
									</>
								) : (
									<>
										<strong>+</strong> {gettext('Plus de détails')}
									</>
								)}
							</p>
						</div>
					)}
				</div>

				<div className="card public_axe aim_container" style={{ padding: '2rem', margin: '1rem', width: '97%', borderRadius: '25px' }}>
					<div className="points_title mb-3">
						<div className="d-flex align-items-center">
							<h2 className="txt_line title--h2">{gettext('Objectifs recommandés')}</h2>
						</div>
					</div>

					{this.props.aims.slice(0, this.state.aimsDetails ? this.props.aims.length : 3).map((aim, index) => {
						return (
							aim.description && (
								<div className="aim_answer_container row mb-2 mx-2 mt-4">
									<div className="icon">
										<i className="bi bi-bullseye align-self-center" style={{ color: getColors(aim.category, [1]) }}></i>
									</div>
									<div className="aim_answer">
										<div className="mxt--h4">{aim.custom_title ? aim.custom_title : aim.subcategory}</div>
										<div className="mxt--small">{aim.description}</div>
									</div>
								</div>
							)
						);
					})}
					{this.props.aims.length === 0 && this.props.CommentsLoaded && <div className="mb-3">{gettext('Aucun objectif')}</div>}
					{/*<div className="mb-3" style={{ display: this.props.CommentsLoaded ? 'none' : 'block' }}>*/}
					{/*	{gettext('Chargement')}*/}
					{/*</div>*/}

					{this.props.aims.length > 3 && (
						<div
							className="d-flex justify-content-center mt-4"
							style={{ color: getColors(this.props.aims[0].category, [1]), cursor: 'pointer' }}
							onClick={() => this.setState({ aimsDetails: !this.state.aimsDetails })}
						>
							<p className="m-0">
								{this.state.aimsDetails ? (
									<>
										<strong>-</strong> {gettext('Masquer les détails')}
									</>
								) : (
									<>
										<strong>+</strong> {gettext('Plus de détails')}
									</>
								)}
							</p>
						</div>
					)}
				</div>
			</React.Fragment>
		);
	}
}
