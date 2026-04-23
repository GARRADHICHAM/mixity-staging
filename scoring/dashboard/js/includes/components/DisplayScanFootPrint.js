import React, { useState, useEffect } from 'react';
import { Card } from 'react-bootstrap';
import { Skeleton } from '@mui/material';
import Footprint from '../../../../../mixity/dashboard/js/includes/Footprint';

export default function DisplayScanFootPrint(props) {
	const [radarData, setRadarData] = useState(null);
	const [user, setUser] = useState(null);

	const getUser = async () => {
		const response = await fetch(`/api/get_profile/`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});
		if (response.status === 200) {
			const data = await response.json();
			setUser(data);
		} else {
			console.log(response);
		}
	};

	useEffect(() => {
		getUser();
		if (props.data.radarData) {
			setRadarData(props.data.radarData);
		}
	}, [props.data.radarData]);

	if (!radarData || !user) {
		return <div></div>;
	}

	return (
		<div className="d-flex flex-column" style={{ maxWidth: '50%' }}>
			<h1 className="mxt--large-bold mb-3">{gettext('Votre empreinte')}</h1>
			<Card className="flex-grow-1">
				<Card.Header className="d-flex justify-content-between m-0 p-0"
							 style={{ background: 'none', border: 'none' }}>
					{/* Structure name & Global Score */}
					<div className="flex-grow-1 relative d-flex justify-content-start align-items-center">
						<img
							src={user.photo != '' && user.photo != null ? user.photo : '/static/icon/basic_profile_pic.svg'}
							alt="profile_picture"
							style={{ width: '45px', marginBottom: '0.5rem', marginRight: '6%', borderRadius: '90px' }}
						/>
						<div className="d-flex flex-column">
							<Card.Title className="d-flex ">{user.first_name + ' ' + user.last_name}</Card.Title>
							<Card.Subtitle
								style={{
									fontSize: '14px',
								}}
							>
								{user.job}
							</Card.Subtitle>
						</div>
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
						<Card.Text className="mxt--large-bold m-0" style={{ color: '#181B3D' }}>
							{Math.round(radarData.global)}
							<span className="mxt--small-bold" style={{ color: '#181B3D' }}>
								/100
							</span>
						</Card.Text>
					</div>
				</Card.Header>

				<Card.Body className="d-flex justify-content-between align-items-center m-0 mt-4 p-0">
					{/* Jauges Body */}
					<div className="d-flex flex-column" style={{ width: '47%' }}>
						{
							radarData.measures
								.filter((cat) => cat.key != 'bonus_posture')
								.map((cat) => (
									<React.Fragment key={cat.key}>
										<div className="d-flex justify-content-between align-items-center mb-1">
											<h3
												className="fw-medium mb-0"
												style={{
													fontSize: '.9rem',
												}}
											>
												{gettext(cat.label)}
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
												className="progress-bar-inner"
												style={{
													width: `${cat.value}%`,
													height: '10px',
													backgroundColor: cat.color,
													borderRadius: '5px',
												}}
											></div>
										</div>
									</React.Fragment>
								))
						}
					</div>
					{/* Footprint Body */}
					<Footprint
						key={radarData.measures[0].value}
						data={{
							id: 'radar_543',
							isCategoryEvaluation: false,
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
		</div>
	);
}
