import React, { Component } from 'react';
import { CircularProgressbar, CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import { getColors } from './ColorData';

class AssessSubCategoryScore extends Component {
	constructor(props) {
		super(props);
	}

	render() {
		return (
			<React.Fragment>
				{/*  Subcategory name  */}
				{/* score circular progress bars */}
				<div className="m-auto" style={{ width: '80%' }}>
					<span className="d-block text-center mb-3">{this.props.subCatName}</span>
					{this.props.benchmarkActive ?
						<CircularProgressbarWithChildren
							value={this.props.subCatGlobalPercent}
							strokeWidth={3}
							counterClockwise={true}
							styles={buildStyles({
								pathColor: getColors('meanscore_global', [1]),
								strokeLinecap: 'round',
								trailColor: '#F0F3FF',
							})}
						>
							{/* Score comparing to all the structures circular progress bars */}
							<div style={{ width: '84%' }}>
								<CircularProgressbarWithChildren
									value={this.props.subCatSectorPercent}
									strokeWidth={3}
									counterClockwise={true}
									styles={buildStyles({
										pathColor: getColors('meanscore_sector', [1]),
										strokeLinecap: 'round',
										trailColor: '#F0F3FF',
									})}
								>
									<div style={{ width: '84%' }}>
										<CircularProgressbarWithChildren
											value={this.props.subCatPercent}
											strokeWidth={8}
											counterClockwise={true}
											styles={buildStyles({
												pathColor: this.props.subCatColor,
												strokeLinecap: 'round',
												trailColor: '#F0F3FF',
											})}
										>
										<span className="fw-bold"
											  style={{ fontSize: '1rem' }}>{`${this.props.subCatPercent}%`}</span>
										</CircularProgressbarWithChildren>
									</div>
								</CircularProgressbarWithChildren>
							</div>
						</CircularProgressbarWithChildren>
						:
						<CircularProgressbarWithChildren
							value={this.props.subCatPercent}
							strokeWidth={8}
							counterClockwise={true}
							styles={buildStyles({
								pathColor: this.props.subCatColor,
								strokeLinecap: 'round',
								trailColor: '#F0F3FF',
							})}
						>
							<span className="fw-bold"
								  style={{ fontSize: '1rem' }}>{`${this.props.subCatPercent}%`}</span>
						</CircularProgressbarWithChildren>
					}
				</div>
				{/*  Remaining scores description  */}
				{this.props.benchmarkActive &&
					<div className="d-flex row-flex justify-content-between align-items-center mt-4"
						 style={{ width: '100%' }}>
						<div className="d-flex row-flex" style={{ width: '50%' }}>
							<div style={{ width: '20%', marginRight: '.5rem' }}>
								<CircularProgressbar value={10} background
													 styles={buildStyles({ backgroundColor: getColors('meanscore_global', [1]) })} />
							</div>
							<span className="fw-bold">
								{this.props.subCatGlobalPercent}
								<span>%</span>
							</span>
						</div>
						<div className="d-flex row-flex justify-content-end" style={{ width: '50%' }}>
							<div style={{ width: '20%', marginRight: '.5rem' }}>
								<CircularProgressbar value={10} background
													 styles={buildStyles({ backgroundColor: getColors('meanscore_sector', [1]) })} />
							</div>
							<span className="fw-bold">
								{this.props.subCatSectorPercent}
								<span>%</span>
							</span>
						</div>
					</div>
				}
			</React.Fragment>
		)
			;
	}
}

export default AssessSubCategoryScore;
