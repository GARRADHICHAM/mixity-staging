import React, { Component } from 'react';
import { Card } from 'react-bootstrap';
import { Skeleton } from '@mui/material';
import Footprint from '../../../../../mixity/dashboard/js/includes/Footprint';
import GapChart from '../GapChart';

class DisplayFootprint extends Component {
	constructor(props) {
		super(props);
		this.state = {
			benchmark_toggled: false,
		}
	}

	getYear(evaluationDate) {
		let evaluationDate_ = new Date(evaluationDate);
		return evaluationDate_.getFullYear();
	}

	handleToggle = () => {
		const benchmark = document.getElementById('benchmark');

		if (this.state.benchmark_toggled)
			benchmark.style.display = 'none'
		else 
			benchmark.style.display = 'flex'
		this.setState(() => {
			return {
				benchmark_toggled: !this.state.benchmark_toggled,
			};
		})
	}

	render() {
		const { evaluation, entity, global_score_delta, mean_score, mean_score_in_business_line, scoreCategoriesLoaded, scoreCategories, radarData } = this.props;
		return (
			<>
				{/* Footprint Block */}
				<div className="d-flex flex-column" style={{ maxWidth: '50%' }}>
					<h1 className="mxt--large-bold mb-3 d-flex justify-content-between align-items-end">
						{evaluation && evaluation.is_validated_by_admin ? (
							<>
								{gettext('Votre empreinte') + ' ' + this.getYear(evaluation.modified_by_user_date)}
								<div className="d-flex m-0 me-3 p-0 fw-medium align-items-center" style={{ fontSize: '16px' }}>
									{gettext('Benchmark')}
									<input
										type="checkbox"
										onClick={this.handleToggle}
										style={{ marginRight: '8px', marginLeft: '8px' }}
									></input>
								</div>
							</>
						) : (
							gettext('Votre empreinte')
						)}
						{' '}
					</h1>
					{evaluation && evaluation.is_validated_by_admin ? (
						<Card className="flex-grow-1">
							<Card.Header className="d-flex justify-content-between m-0 p-0" style={{ background: 'none', border: 'none' }}>
								{/* Structure name & Global Score */}
								<div className="d-flex flex-column flex-grow-1 relative">
									{evaluation.is_human ? (
										<Card.Title className="d-flex align-items-center">
											<span style={{ marginRight: '10px' }} className="icon-footprint-human"></span>
											Mixity Human
										</Card.Title>
									) : evaluation.is_scan ? (
											<Card.Title className="d-flex align-items-center">
												<span style={{ marginRight: '10px' }} className="mxt-icon--32 icon-footprint-scan color-diag"></span>
												Mixity Scan
											</Card.Title>
										) : (
											<Card.Title>
												<span style={{ marginRight: '10px' }} className="mxt-icon--32 icon-offer-diag color-diag"></span>
												Mixity Diag
											</Card.Title>
										)
									}
									<Card.Subtitle
										style={{
											fontSize: '14px',
											marginLeft: '31px',
										}}
									>
										{entity.name}
									</Card.Subtitle>
								</div>

								<div className="d-flex flex-column flex-grow-1 align-items-end relative">
									<Card.Title
										className="mxt--small m-0 text-end"
										style={{
											color: 'rgba(144, 148, 170, 1)',
										}}
									>
										{gettext('Score Diversité & Inclusion')}
									</Card.Title>
									<Card.Text className="d-flex justify-content-between gap-3">
										<span className="justify-content-between gap-3" id="benchmark" style={{ display: 'none'}}>
											<div className="mxt--large-bold d-flex flex-column text-end" style={{ color: '#F2A71B'}}>
												<span className="d-flex align-items-end">
													{Math.round(mean_score_in_business_line)}
													<span className="mxt--small-bold" style={{ color: '#F2A71B' }}>
														/100
													</span>
												</span>
												<span className="mxt--small" style={{ color: '#F2A71B' }}>
													{gettext('Secteur')}
												</span>
											</div>
											<div className="mxt--large-bold d-flex flex-column text-end" style={{ color: '#863C63'}}>
												<span className="d-flex align-items-end">
													{Math.round(mean_score)}
													<span className="mxt--small-bold" style={{ color: '#863C63' }}>
														/100
													</span>
												</span>
												<span className="mxt--small" style={{ color: '#863C63' }}>
													{gettext('Global')}
												</span>
											</div>
										</span>
										<span className="mxt--large-bold" style={{ color: '#181B3D'}}>
											{Math.round(global_score_delta)}
											<span className="mxt--small-bold" style={{ color: '#181B3D' }}>
												/100
											</span>
										</span>
									</Card.Text>
								</div>
							</Card.Header>
							<Card.Body className="d-flex justify-content-between align-items-center m-0 mt-4 p-0">
								{/* Jauges Body */}
								<div className="d-flex flex-column" style={{ width: '47%' }}>
									{scoreCategoriesLoaded === true
										? scoreCategories
												.filter((cat) => cat.category.slug != 'all' && cat.category.slug != 'csrd')
												.map((cat) => (
													<React.Fragment>
														<div className="d-flex justify-content-between align-items-center mb-1">
															<h3
																className="fw-medium mb-0"
																style={{
																	fontSize: '.9rem',
																}}
															>
																{gettext(cat.category.name)}
															</h3>
															<p
																className="fw-medium mb-0"
																style={{
																	fontSize: '.9rem',
																}}
															>{`${Math.round(Number(cat.value))} %`}</p>
														</div>
														<div
															className="w-100 progress-bar mb-3"
															style={{
																height: '10px',
																backgroundColor: '#E6E8EC',
																borderRadius: '5px',
															}}
														>
															<div
																class="progress-bar-inner"
																style={{
																	width: `${cat.value}%`,
																	height: '10px',
																	backgroundColor: cat.category.color,
																	borderRadius: '5px',
																}}
															></div>
														</div>
													</React.Fragment>
												))
										: [0, 0, 0, 0, 0].map((cat) => (
												<React.Fragment>
													<div className="d-flex justify-content-between align-items-center">
														<Skeleton
															variant="text"
															width={140}
															sx={{
																fontSize: '.9rem',
															}}
														/>
														<Skeleton
															variant="text"
															width={34}
															sx={{
																fontSize: '.9rem',
															}}
														/>
													</div>
													<Skeleton
														variant="rectangular"
														height={10}
														sx={{
															marginTop: '.5rem',
															marginBottom: '1rem',
														}}
													/>
												</React.Fragment>
											))}
								</div>
								{/* Footprint Body */}
								<Footprint
									key={radarData.measures[0].value}
									data={{
										id: 'radar_' + evaluation.pk,
										isCategoryEvaluation: evaluation.is_category_evaluation,
										measures: radarData,
										mirror: {},
										enableLegend: true,
										enableLinks: false,
										horizontal: true,
									}}
								/>
							</Card.Body>
							<Card.Footer className="m-0 p-0 py-4" style={{ background: 'none', border: 'none' }}>
								{/* Mixity Watermark  */}
								<div className="d-flex justify-content-end relative">
									<img src={'/static/img/logo-mixity.svg'} alt="Logo Mixity" className="radar_watermark" />
								</div>
							</Card.Footer>
						</Card>
					) : (
						<div>
							<img src={'/static/img/footprint_not_available.png'} alt="Image Empreinte non disponible" />
						</div>
					)}
				</div>
			</>
		);
	}
}

export default DisplayFootprint;
