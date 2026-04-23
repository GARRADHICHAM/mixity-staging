import React, { useState, useEffect } from 'react';
import { Card } from 'react-bootstrap';

export default function DisplaySkills(props) {
	const [skills, setSkills] = useState(null);

	const skillsLevels = [
		{ rangeMin: 75, rangeMax: 100, color: '#002944', image: 'Maitrisee.svg', level: gettext('Maîtrisée') },
		{ rangeMin: 75, rangeMax: 100, color: '#002944', image: 'Acquise.svg', level: gettext('Acquise') },
		{ rangeMin: 50, rangeMax: 75, color: '#ffcfc9', image: 'Approfondir.svg', level: gettext('À approfondir') },
		{ rangeMin: 25, rangeMax: 50, color: '#9AFFE5', image: 'Developper.svg', level: gettext('À développer') },
		{ rangeMin: 0, rangeMax: 25, color: '#ffcfc9', image: 'Acquerir.svg', level: gettext('À acquérir') },
	];

	const getSkillLevel = (skills) => {
		Object.values(skills).map(skill => {
			const skill_level = skillsLevels.find(obj => skill.score >= obj.rangeMin && skill.score <= obj.rangeMax)
			skill["image"] = skill_level["image"]
			skill["level"] = skill_level["level"]
		})
		return skills
	}

	useEffect(() => {
		if (props.data.skills)
			setSkills(getSkillLevel(props.data.skills))
	}, [props.data.skills]);

	if (!skills) {
		return <div></div>;
	}

	return (
		<div className="d-flex flex-column mb-4">
			<h3 className="fw-medium mb-4">{gettext('Mes Compétences')}</h3>
			<div className="d-flex justify-content-around flex-wrap" style={{gap:"1.5rem"}}>
				{Object.values(skills).map((skill, key) => (
					<Card className="card-profile-skills flex-wrap mb-2 mr-2" key={key} style={{ flexGrow:1 }}>
						<Card.Body className="d-flex justify-content-around align-items-center flex-column">
							<Card.Title>{gettext(skill.name)}</Card.Title>
							<img className="p-2" style={{ width:"auto" }} src={`/static/img/scan/${skill.image}`} alt={skill.name} />
							<Card.Subtitle
								style={{
									fontSize: '14px',
									marginTop: '10px',
								}}
							>
								{gettext(skill.level)}
							</Card.Subtitle>
						</Card.Body>
					</Card>
				))}
			</div>
		</div>
	);
}
