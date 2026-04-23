import React, { useState } from 'react';
import { getColors } from '../ColorData';


export default function DisplayIAScanAnalysis(props) {
    const [strengthsDetails, setStrengthsDetails] = useState(false);
    const [weaknessesDetails, setWeaknessesDetails] = useState(false);
    const [aimsDetails, setAimsDetails] = useState(false);

    return (
        <div className="w-100 my-5 d-flex flex-column gap-4">
            <div className="d-flex justify-content-between flex-wrap">
                <div style={{ width: '49%' }}>
                    <div className="card p-4 w-100" style={{ minHeight: '100%', maxHeight: 'fit-content'}}>
                        <div>
                            <h3 className="txt_line title--h2">
                                {gettext("Points forts")}
                            </h3>
                        </div>
                        <div>
                            {props.data.analysis.strength.slice(0, 3).map((strength) => {
                                return (
                                    <div className="strenght_answer_container row mb-2 mx-2 mt-4">
                                        <div className="icon">
                                            <i className="bi bi-hand-thumbs-up align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                        </div>
                                        <div className="strenght_answer">
                                            <div className="mxt--normal">{strength}</div>
                                        </div>
                                    </div>
                                );
                            })}
                            {strengthsDetails && (
                                <>
                                    {props.data.analysis.strength.slice(3).map((strength) => {
                                        return (
                                            <div className="strenght_answer_container row mb-2 mx-2 mt-4">
                                                <div className="icon">
                                                    <i className="bi bi-hand-thumbs-up align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                                </div>
                                                <div className="strenght_answer">
                                                    <div className="mxt--normal">{strength}</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </>
                            )}
                            {props.data.analysis.strength.length > 3 && (
                                <div
                                    className="d-flex justify-content-center"
                                    style={{ color: getColors(props.data.category, [1]), cursor: 'pointer' }}
                                    onClick={() => setStrengthsDetails(!strengthsDetails )}
                                >
                                    <p className="m-0">
                                        {strengthsDetails ? (
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
                    </div>
                </div>
                <div style={{ width: '49%' }}>
                    <div className="card p-4 w-100" style={{ minHeight: '100%', maxHeight: 'fit-content'}}>
                        <div>
                            <h3 className="txt_line title--h2">
                                {gettext("Axes d'amélioration")}
                            </h3>
                        </div>
                        <div>
                            {props.data.analysis.weakness.slice(0, 3).map((weakness) => {
                                return (
                                    <div className="weakness_answer_container row mb-2 mx-2 mt-4">
                                        <div className="icon">
                                            <i className="bi bi-award align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                        </div>
                                        <div className="weakness_answer">
                                            <div className="mxt--normal">{weakness}</div>
                                        </div>
                                    </div>
                                );
                            })}
                            {weaknessesDetails && (
                                <>
                                    {props.data.analysis.weakness.slice(3).map((weakness) => {
                                        return (
                                            <div className="strenght_answer_container row mb-2 mx-2 mt-4">
                                                <div className="icon">
                                                    <i className="bi bi-hand-thumbs-up align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                                </div>
                                                <div className="strenght_answer">
                                                    <div className="mxt--normal">{weakness}</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </>
                            )}
                            {props.data.analysis.weakness.length > 3 && (
                                <div
                                    className="d-flex justify-content-center"
                                    style={{ color: getColors(props.data.category, [1]), cursor: 'pointer' }}
                                    onClick={() => setWeaknessesDetails(!weaknessesDetails )}
                                >
                                    <p className="m-0">
                                        {weaknessesDetails ? (
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
                    </div>
                </div>
            </div>
            <div className="w-100">
                <div className="card p-4 w-100">
                    <div>
                        <h3 className="txt_line title--h2">
                            {gettext("Objectifs")}
                        </h3>
                    </div>
                    <div className="d-flex">
                        <div className="w-50">
                            {props.data.analysis.aim.slice(props.data.analysis.aim.length / 2).slice(0, 3).map((aim) => {
                                return (
                                    <div className="aim_answer_container row mb-2 mx-2 mt-4">
                                        <div className="icon">
                                            <i className="bi bi-bullseye align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                        </div>
                                        <div className="aim_answer">
                                            <div className="mxt--normal">{aim}</div>
                                        </div>
                                    </div>
                                );
                            })}
                            {aimsDetails && (
                                <>
                                    {props.data.analysis.aim.slice(props.data.analysis.aim.length / 2).slice(3).map((aim) => {
                                        return (
                                            <div className="aim_answer_container row mb-2 mx-2 mt-4">
                                                <div className="icon">
                                                    <i className="bi bi-bullseye align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                                </div>
                                                <div className="aim_answer">
                                                    <div className="mxt--normal">{aim}</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </>
                            )}
                        </div>
                        <div className="w-50">
                            {props.data.analysis.aim.slice(0, props.data.analysis.aim.length / 2).slice(0, 3).map((aim) => {
                                return (
                                    <div className="aim_answer_container row mb-2 mx-2 mt-4">
                                        <div className="icon">
                                            <i className="bi bi-bullseye align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                        </div>
                                        <div className="aim_answer">
                                            <div className="mxt--normal">{aim}</div>
                                        </div>
                                    </div>
                                );
                            })}
                            {aimsDetails && (
                                <>
                                    {props.data.analysis.aim.slice(0, props.data.analysis.aim.length / 2).slice(3).map((aim) => {
                                        return (
                                            <div className="aim_answer_container row mb-2 mx-2 mt-4">
                                                <div className="icon">
                                                    <i className="bi bi-bullseye align-self-center" style={{ color: getColors(props.data.category, [1]) }}></i>
                                                </div>
                                                <div className="aim_answer">
                                                    <div className="mxt--normal">{aim}</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </>
                            )}
                        </div>
                        {props.data.analysis.aim.length > 3 && (
                            <div
                                className="d-flex justify-content-center"
                                style={{ color: getColors(props.data.category, [1]), cursor: 'pointer' }}
                                onClick={() => setAimsDetails(!aimsDetails )}
                            >
                                <p className="m-0">
                                    {aimsDetails ? (
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
                </div>
            </div>
        </div>
    );
}
