import React, { Component } from 'react';
import { Modal } from 'react-bootstrap';
import { getColors } from './ColorData';

export default class ProgressBarIndicator extends Component {
	constructor(props) {
		super(props);
		this.state = {
			showModal: false,
			activeBenchmark: false,
		};
	}

	legendDescItem(color, value, isEntity = false) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? <span className="legend_value fw-bold">{value}</span> : <span className="legend_value">{value}</span>}
			</div>
		);
	}

	render() {
		return (
			<div className="progressbar_container d-flex flex-column align-items-center">
				<div className="progressbar_list w-100">
					{this.props.data.values &&
						this.props.data.values.slice(0, 6).map((value, index) => {
							// afficher toutes les réponses
							return (
								<React.Fragment key={index}>
									<div>
										<div className="d-flex justify-content-between align-items-start mb-1">
											<h3 className="fw-medium" style={{ width: '85%', fontSize: '.9rem' }}>
												{index + 1}. {this.props.data.selector_labels[index]}
											</h3>
											<p
												className="fw-medium mb-0 text-end"
												style={{ width: '15%', fontSize: '.9rem' }}
											>{`${Math.round(Number(value))} %`}</p>
										</div>
										<div
											className={`w-100 progress-bar ${!this.state.activeBenchmark ? 'mb-3' : 'mb-2'}`}
											style={{ height: '20px', backgroundColor: '#E6E8EC', borderRadius: '10px' }}
										>
											<div
												className="progress-bar-inner"
												style={{
													width: `${value}%`,
													height: '20px',
													backgroundColor: getColors(this.props.category, [1]),
													borderRadius: '10px',
												}}
											></div>
										</div>
										{/*{this.state.activeBenchmark &&*/}
										{/*  <React.Fragment>*/}
										{/*    <div className="w-100 progress-bar mb-1" style={{height: "10px", backgroundColor: "#E6E8EC", borderRadius: "5px"}}>*/}
										{/*      <div className="progress-bar-inner" style={{width: `${this.props.data.meanscore_sector_values}%`, height: "10px", backgroundColor: getColors("meanscore_sector", [1]), borderRadius: "5px"}}></div>*/}
										{/*      <div className="relative fw-medium mb-0" style={{fontSize: ".8rem"}}>{`${Math.round(Number(this.props.data.meanscore_sector_value))} %`}</div>*/}
										{/*    </div>*/}
										{/*    <div className="w-100 progress-bar mb-2" style={{height: "10px", backgroundColor: "#E6E8EC", borderRadius: "5px"}}>*/}
										{/*      <div className="progress-bar-inner" style={{width: `${this.props.data.meanscore_global_values}%`, height: "10px", backgroundColor: getColors("meanscore_global", [1]), borderRadius: "5px"}}></div>*/}
										{/*      <div className="relative fw-medium mb-0" style={{fontSize: ".8rem"}}>{`${Math.round(Number(this.props.data.meanscore_sector_value))} %`}</div>*/}
										{/*    </div>*/}
										{/*  </React.Fragment>*/}
									</div>
								</React.Fragment>
							);
						})}
				</div>
				{/*{this.state.activeBenchmark &&*/}
				{/*  <React.Fragment>*/}
				{/*        <div className='d-flex'>*/}
				{/*            <div className='legend_item px-2'>{this.legendDescItem(getColors(this.props.category, [1]), gettext("Entreprise"))}</div>*/}
				{/*            <div className='legend_item px-2'>{this.legendDescItem(getColors("meanscore_sector", [1]), gettext("Moyenne Secteur"))}</div>*/}
				{/*            <div className='legend_item px-2'>{this.legendDescItem(getColors("meanscore_global", [1]), gettext("Moyenne Globale"))}</div>*/}
				{/*        </div>*/}
				{/*  </React.Fragment>*/}
				{/*}*/}
				{/*{this.props.isHuman &&*/}
				{/*    <React.Fragment>*/}
				{/*        <div className="d-flex gap-2 justify-content-center align-items-center my-3">*/}
				{/*            <div className="d-flex align-items-center">*/}
				{/*                <input type="checkbox" id={`input-filter-${this.props.data.title}`} value={this.state.activeBenchmark} onClick={() => this.changeBenchmark()}></input>*/}
				{/*                <label className="ps-2">{gettext("Afficher le Benchmark")}</label>*/}
				{/*            </div>*/}
				{/*        </div>*/}
				{/*    </React.Fragment>*/}
				{/*}*/}
				{this.props.data.values.length > 6 && (
					<button className="indicator_details" onClick={() => this.setState({ showModal: true })}>
						{gettext('Plus de détails')}
					</button>
				)}
				<Modal
					size="lg"
					show={this.state.showModal}
					onHide={() => this.setState({ showModal: false })}
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050', width: '100%' }}
					className="indicator_modal m-0 p-0"
				>
					<Modal.Header closeButton>
						<Modal.Title id="contained-modal-title-vcenter" className="text-center">
							{this.props.data.title}
						</Modal.Title>
					</Modal.Header>
					<Modal.Body>
						{this.props.data.values &&
							this.props.data.values.map((value, index) => {
								return (
									<React.Fragment>
										<React.Fragment key={index}>
											<div>
												<div className="d-flex justify-content-between align-items-center mb-1">
													<h3 className="fw-medium" style={{ width: '85%', fontSize: '.9rem' }}>
														{index + 1}. {this.props.data.selector_labels[index]}
													</h3>
													<p
														className="fw-medium mb-0 text-end"
														style={{ width: '15%', fontSize: '.9rem' }}
													>{`${Math.round(Number(value))} %`}</p>
												</div>
												<div
													className={`w-100 progress-bar ${!this.state.activeBenchmark ? 'mb-3' : 'mb-2'}`}
													style={{ height: '20px', backgroundColor: '#E6E8EC', borderRadius: '10px' }}
												>
													<div
														className="progress-bar-inner"
														style={{
															width: `${value}%`,
															height: '20px',
															backgroundColor: getColors(this.props.category, [1]),
															borderRadius: '10px',
														}}
													></div>
												</div>
												{this.state.activeBenchmark && (
													<React.Fragment>
														<div
															className="w-100 progress-bar mb-1"
															style={{ height: '10px', backgroundColor: '#E6E8EC', borderRadius: '5px' }}
														>
															<div
																className="progress-bar-inner"
																style={{
																	width: `${this.props.data.meanscore_sector_values}%`,
																	height: '10px',
																	backgroundColor: getColors('meanscore_sector', [1]),
																	borderRadius: '5px',
																}}
															></div>
															<div
																className="relative fw-medium mb-0"
																style={{ fontSize: '.8rem' }}
															>{`${Math.round(Number(this.props.data.meanscore_sector_value))} %`}</div>
														</div>
														<div
															className="w-100 progress-bar mb-2"
															style={{ height: '10px', backgroundColor: '#E6E8EC', borderRadius: '5px' }}
														>
															<div
																className="progress-bar-inner"
																style={{
																	width: `${this.props.data.meanscore_global_values}%`,
																	height: '10px',
																	backgroundColor: getColors('meanscore_global', [1]),
																	borderRadius: '5px',
																}}
															></div>
															<div
																className="relative fw-medium mb-0"
																style={{ fontSize: '.8rem' }}
															>{`${Math.round(Number(this.props.data.meanscore_sector_value))} %`}</div>
														</div>
													</React.Fragment>
												)}
											</div>
										</React.Fragment>
										{/*{this.state.activeBenchmark &&
                        <React.Fragment>
                              <div className='d-flex'>
                                  <div className='legend_item px-2'>{this.legendDescItem(getColors(this.props.category, [1]), gettext("Entreprise"))}</div>
                                  <div className='legend_item px-2'>{this.legendDescItem(getColors("meanscore_sector", [1]), gettext("Moyenne Secteur"))}</div>
                                  <div className='legend_item px-2'>{this.legendDescItem(getColors("meanscore_global", [1]), gettext("Moyenne Globale"))}</div>
                              </div>
                        </React.Fragment>
                      }*/}
									</React.Fragment>
								);
							})}
					</Modal.Body>
				</Modal>
			</div>
		);
	}
}
