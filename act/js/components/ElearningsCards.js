import React, { useState, useEffect } from 'react';
import { Card } from 'react-bootstrap';

function ElearningsCards({ elearnings, placeholder, environmentUrl }) {
	const hideElements = (number, elements) => {
		if (elements.length >= number) {
			let tabElements = [];
			for (let i = 0; i < number; i++) {
				tabElements.push(elements[i]);
			}
			return tabElements;
		}
		return;
	};

	const handleCardClick = (slug) => {
		let newUrl = environmentUrl + '/elearning/' + `${slug}/details`;
		window.location.href = newUrl;
	};

	return (
		<div className="elearning-cards-container">
			{elearnings.length > 0 ? (
				elearnings.map((elearning) => (
					<Card
						key={elearning.slug}
						className="p-0 elearning-card"
						style={{
							borderRadius: '16px',
							borderColor: '#DEDFEA',
							backgroundColor: '#fff',
						}}
						onClick={() => handleCardClick(elearning.slug)}
					>
						<Card.Img
							className="catalogue-img"
							style={{ objectFit: 'cover' }}
							variant="top"
							src={elearning.photo || '/static/img/elearning/placeholder_1.svg'}
						/>
						<Card.Body className="p-4 elearning-card-body">
							<div className="d-flex flex-wrap mb-2 flex-column w-100">
								<div className="elearning-tags">
									{elearning.category.map((cat) => (
										<Card.Text
											key={cat.slug}
											className="border py-1 px-2 mb-0 me-2 category-tag"
											style={{
												borderRadius: '24px',
												width: 'fit-content',
												fontSize: '12px',
												fontWeight: '500',
												letterSpacing: '-0.02rem',
												color: cat.color,
											}}
										>
											<i className="bi bi-circle-fill me-1 pe-1" style={{ fontSize: '8px', top: '1%' }}></i>
											{gettext(cat.name)}
										</Card.Text>
									))}
									{hideElements(1, elearning.notions) &&
										(() => {
											const notions = hideElements(1, elearning.notions);
											return notions.map((notion) => (
												<Card.Text
													key={notion.slug}
													className="border py-1 px-2 mb-0 me-2 notion-text mb-0"
													style={{
														borderRadius: '24px',
														width: 'fit-content',
														fontSize: '12px',
														fontWeight: '500',
														letterSpacing: '-0.02rem',
													}}
												>
													{gettext(notion.label)}
												</Card.Text>
											));
										})()}

									{elearning.notions.length > 1 && (
										<Card.Text
											className="border py-1 px-2 mb-0 me-2 other-notions-text mb-0"
											style={{
												borderRadius: '24px',
												width: 'fit-content',
												fontSize: '12px',
												fontWeight: '500',
												letterSpacing: '-0.02rem',
											}}
										>
											{`+${elearning.notions.length - 1}`}
										</Card.Text>
									)}
								</div>
								<div className="mt-3 w-100">
									<Card.Text className="title-text">{elearning.title}</Card.Text>
									<Card.Text className="summary-text">{elearning.summary}</Card.Text>
								</div>
							</div>
							<div className="elearning-card-bottom">
								<div className="time-target-container" style={{ marginBottom: '0.5rem' }}>
									<div className="d-flex">
										<img className="elearning-icon" src="/static/img/Time.svg" />
										<Card.Text className="time-text">{elearning.time}</Card.Text>
									</div>
									<div className="d-flex">
										<img className="elearning-icon" src="/static/img/Public.svg" />
										<Card.Text className="target-text">{elearning.target}</Card.Text>
									</div>
								</div>
								{elearning.languages.length > 0 && (
									<div className="d-flex align-items-start" style={{ marginRight: '0.5rem' }}>
										<img className="elearning-icon" src="/static/img/Web.svg" alt="Language icon" />

										{hideElements(2, elearning.languages) &&
											(() => {
												const languages = hideElements(2, elearning.languages);
												const languagesLabels = languages.map((language) => language.label);

												return <Card.Text className="language-text">{languagesLabels.join(', ')}</Card.Text>;
											})()}

										{elearning.languages.length > 2 && (
											<Card.Text key="other-keywords" className="language-text">
												&nbsp;+{elearning.languages.length - 2}
											</Card.Text>
										)}
									</div>
								)}
								<div className="keywords-list">
									{hideElements(2, elearning.keywords) &&
										(() => {
											const keywords = hideElements(2, elearning.keywords);
											return keywords.map((keyword) => (
												<Card.Text key={keyword.slug} className="keywords-text border">
													{keyword.label}
												</Card.Text>
											));
										})()}

									{elearning.keywords.length > 1 && (
										<Card.Text key="other-keywords" className="keywords-text border">
											{`+${elearning.keywords.length - 1}`}
										</Card.Text>
									)}
								</div>
							</div>
						</Card.Body>
					</Card>
				))
			) : (
				<div className="placeholder">
					<p>{gettext(placeholder)}</p>
				</div>
			)}
		</div>
	);
}

export default ElearningsCards;
