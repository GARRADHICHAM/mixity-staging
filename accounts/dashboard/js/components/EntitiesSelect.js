import React, { Component } from 'react';
import { Form } from 'react-bootstrap';

class EntitySelector extends Component {
	constructor(props) {
		super(props);
		this.state = {
			entities: props.entities,
		};
	}

	renderEntities(entities, level = 0) {
		return entities.map((entity, index) =>
			entity.display ? (
				<div key={index}>
					<style>
						{`
                            .entity-category {
                                background-color: #FFFFFF !important;
                                border-color: #181B3D !important;
                            }
                            .entity-category:hover {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                            }
                            .entity-category:focus {
                                background-color: #FFFFFF !important;
                                border-color: #181B3D !important;
                            }
                            .entity-category:active {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                            }
                            .entity-category:checked {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                                visibility: visible;
                                background-size: 8.5px;
                                background-repeat: no-repeat;
                                background-position: center center;

                            }

                            .entity-disabled {
                                background-color: #F3F3FC !important;
                                border-color: #F3F3FC !important;
                            }

                            .entity-disabled:hover {
                                background-color: #F3F3FC !important;
                                border-color: #F3F3FC !important;
                            }

                            .entity-disabled:focus {
                                background-color: #F3F3FC !important;
                                border-color: #F3F3FC !important;
                            }

                            .entity-disabled:active {
                                background-color: #F3F3FC !important;
                                border-color: #F3F3FC !important;
                            }

                            .entity-selected {
                                background-color: #FFFFFF !important;
                                border-color: #181B3D !important;
                            }
                            .entity-selected:hover {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                            }
                            .entity-selected:focus {
                                background-color: #FFFFFF !important;
                                border-color: #181B3D !important;
                            }
                            .entity-selected:active {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                            }
                            .entity-selected:checked {
                                background-color: #181B3D !important;
                                border-color: #181B3D !important;
                                visibility: visible;
                                background-image: url('/static/icon/checkbox_mark.svg');
                                background-size: 8.5px;
                                background-repeat: no-repeat;
                                background-position: center center;

                            }
                        `}
					</style>
					<div style={{ width: '96%', marginLeft: `${level * 20}px` }}>
						<div
							className="d-flex justify-content-between"
							style={{
								padding: '0.5% 1% 0.5% 1%',
								width: `calc(100% - ${level * 20}px)`,
								backgroundColor: entity.childrens[0]?.display ? '#F3F3FC' : '#FFFFFF',
							}}
						>
							<div className="d-flex align-items-center" style={{ width: '100%', fontWeight: 520, cursor: 'pointer' }}>
								<div className="d-flex align-items-center" style={{ paddingRight: '5px' }}>
									<input
										className={entity.selected ? 'entity-selected' : entity.disabled ? 'entity-disabled' : 'entity-category'}
										type={'checkbox'}
										style={{ borderRadius: '4px' }}
										disabled={entity.disabled ? true : false}
										checked={entity.selected ? true : false}
										onChange={() => {
											this.setSelectedEntity(entity, !entity.selected);
										}}
									/>
								</div>
								<div
									className="d-flex justify-content-between"
									style={{ width: '100%' }}
									onClick={() => {
										this.setDisplayEntity(entity, !entity.childrens[0]?.display);
									}}
								>
									{entity.label}
									{entity.childrens.length > 0 && (
										<i
											className="d-flex align-items-center fa fa-chevron-down dropdown-value-icon"
											style={{ transform: entity.childrens[0]?.display ? 'rotate(180deg)' : '' }}
										></i>
									)}
								</div>
							</div>
						</div>
					</div>
					<div>{this.renderEntities(entity.childrens, level + 1)}</div>
				</div>
			) : null,
		);
	}

	setDisableEntity(entity, disabled) {
		if (disabled === undefined) {
			return;
		}
		const new_entites = this.state.entities;

		entity.disabled = disabled;

		entity.childrens.forEach((child) => {
			this.setDisableEntity(child, disabled);
		});

		new_entites.forEach((ent) => {
			if (ent.label === entity.label) {
				ent = entity;
			}
		});
		this.setState({ entities: new_entites });
	}

	unselectEntity(entity) {
		const new_entites = this.state.entities;

		entity.selected = false;
		entity.disabled = false;

		entity.childrens.forEach((child) => {
			this.unselectEntity(child);
		});

		new_entites.forEach((ent) => {
			if (ent.label === entity.label) {
				ent = entity;
			}
		});
		this.setState({ entities: new_entites });
	}

	setSelectedEntity(entity, selected) {
		if (selected === undefined) {
			return;
		}
		this.state.entities.forEach((ent) => {
			this.unselectEntity(ent);
		});
		const new_entites = this.state.entities;

		entity.selected = selected;

		entity.childrens.forEach((child) => {
			this.setDisableEntity(child, selected);
		});

		new_entites.forEach((ent) => {
			if (ent.label === entity.label) {
				ent = entity;
			}
		});
		this.setState({ entities: new_entites });
	}

	setDisplayEntity(entity, display) {
		if (display === undefined) {
			return;
		}
		const new_entites = this.state.entities;

		entity.childrens.forEach((child) => {
			child.display = display;
		});

		new_entites.forEach((ent) => {
			if (ent.label === entity.label) {
				ent = entity;
			}
		});
		this.setState({ entities: new_entites });
	}

	render() {
		return <>{this.renderEntities(this.state.entities)}</>;
	}
}

export default EntitySelector;
