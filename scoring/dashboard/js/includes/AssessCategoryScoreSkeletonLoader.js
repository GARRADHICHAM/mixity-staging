import React, { Component } from 'react';
import { Skeleton } from '@mui/material';

class AssessSubCategoryScoreSkeletonLoader extends Component {
	constructor(props) {
		super(props);
	}

	render() {
		return (
			<div>
				<div className="d-flex flex-column" style={{ width: '26%' }}>
					<Skeleton variant="circular" width={104} height={104} />
					<div className="d-flex row-flex justify-content-between" style={{ width: '100%' }}>
						<div className="d-flex row-flex" style={{ width: '50%' }}>
							<Skeleton variant="text" width={52} />
						</div>
						<div className="d-flex row-flex justify-content-end" style={{ width: '50%' }}>
							<Skeleton variant="text" width={52} />
						</div>
					</div>
				</div>
			</div>
		);
	}
}

export default AssessSubCategoryScoreSkeletonLoader;
