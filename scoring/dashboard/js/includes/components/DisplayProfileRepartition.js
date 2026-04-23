import React, {component} from 'react';
import { getColors, dataLabelColor } from '../ColorData';
import { Modal } from 'react-bootstrap';

class DisplayProfileRepartition extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            showProfileRepartition: false,
            showLevelDetail: [false, false, false, false],
        };
    };

    handleToggle = () => {
        this.setState({ showProfileRepartition: !this.state.showProfileRepartition });
    }

    handleLevelToggle = (level) => {
        let newList = this.state.showLevelDetail;

        newList[level] = !newList[level];
        this.setState({showLevelDetail: newList});
    }

    render() {
        const { data } = this.props;
        return (
            <div className="card d-flex flex-column gap-4">
                <div className="d-flex justify-content-between" style={{ cursor: 'pointer' }} onClick={this.handleToggle}>
                    <h3 className="mxt--normal-bold mb-0">{gettext("Répartition des profils de vos recruteurs (f/h/nb)")}</h3>
                    <div className="d-flex align-items-center px-2">
                        <img
                            style={{
                                transition: 'transform 0.3s',
                                transform: !this.state.showProfileRepartition ? 'rotate(0deg)' : 'rotate(45deg)',
                                width: '30px',
                            }}
                            src={'/static/icon/plus.svg'}
                            alt="+"
                        />
                    </div>
                </div>
                {this.state.showProfileRepartition && (
                    <div className="w-100 d-flex">
                        <div className="d-flex flex-column gap-4" style={{ width: '66%'}}>
                            <div>
                                <div className="pt-1 pb-2 d-flex justify-content-between" style={{ borderBottom: `2px solid ${getColors('repartition_list', [4])[0]}`, cursor: 'pointer' }} onClick={() => this.handleLevelToggle(0)}>
                                    <h3>{gettext("Niveau 1")}</h3>
                                    <div className="d-flex align-items-center px-2">
                                        <img
                                            style={{
                                                transition: 'transform 0.3s',
                                                transform: !this.state.showLevelDetail[0] ? 'rotate(0deg)' : 'rotate(180deg)',
                                                width: '15px',
                                            }}
                                            src={'/static/icon/chevron-down.svg'}
                                            alt="v"
                                        />
                                    </div>
                                </div>
                                {this.state.showLevelDetail[0] && (
                                    <div className="mt-2">
                                        <p className="mxt--small">
                                            {gettext("Vous avez une conscience partielle des enjeux de Diversité et Inclusion et n'êtes pas vraiment engagé.e sur la question.")}
                                            <br/><br/>
                                            {gettext("Nous recommandons de vous renseigner sur les enjeux d'une politique de recrutement inclusive et à vous pencher sur les actions à mettre en place pour garantir l'inclusion. Quand vous vous sentez prêt.e, réfléchissez sur vos possibles biais et comportements et comment ils impactent votre mission et organisation.")}
                                            <br/><br/>
                                            {gettext("Vos maîtres mots pour la suite : ")}
                                            <b>{gettext("curiosité")}</b>
                                            {gettext(" et ")}
                                            <b>{gettext("ouverture")}</b>
                                            {gettext(".")}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div>
                                <div className="pt-1 pb-2 d-flex justify-content-between" style={{ borderBottom: `2px solid ${getColors('repartition_list', [3])[0]}`, cursor: 'pointer' }} onClick={() => this.handleLevelToggle(1)}>
                                    <h3>{gettext("Niveau 2")}</h3>
                                    <div className="d-flex align-items-center px-2">
                                        <img
                                            style={{
                                                transition: 'transform 0.3s',
                                                transform: !this.state.showLevelDetail[1] ? 'rotate(0deg)' : 'rotate(180deg)',
                                                width: '15px',
                                            }}
                                            src={'/static/icon/chevron-down.svg'}
                                            alt="v"
                                        />
                                    </div>
                                </div>
                                {this.state.showLevelDetail[1] && (
                                    <div className="mt-2">
                                        <p className="mxt--small">
                                            {gettext("Vous avez conscience de l’enjeu stratégique que représente la Diversité, l'Équité et l’Inclusion au sein de l’entreprise.")}
                                            <br/><br/>
                                            {gettext("Vous sentez-vous équipé.e et motivé.e pour discuter et agir auprès de vos collègues, pour questionner les comportements et processus existants, y compris les vôtres ? N’hésitez pas à aller au-delà de la stratégie Diversité, Équité et Inclusion et à vous mettre en situation d'apprentissage sur ces questions, même si cela peut être inconfortable.")}
                                            <br/><br/>
                                            {gettext("Vos maîtres mots pour la suite : ")}
                                            <b>{gettext("introspection")}</b>
                                            {gettext(" et ")}
                                            <b>{gettext("engagement")}</b>
                                            {gettext(".")}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div>
                                <div className="pt-1 pb-2 d-flex justify-content-between" style={{ borderBottom: `2px solid ${getColors('repartition_list', [2])[0]}`, cursor: 'pointer' }} onClick={() => this.handleLevelToggle(2)}>
                                    <h3>{gettext("Niveau 3")}</h3>
                                    <div className="d-flex align-items-center px-2">
                                        <img
                                            style={{
                                                transition: 'transform 0.3s',
                                                transform: !this.state.showLevelDetail[2] ? 'rotate(0deg)' : 'rotate(180deg)',
                                                width: '15px',
                                            }}
                                            src={'/static/icon/chevron-down.svg'}
                                            alt="v"
                                        />
                                    </div>
                                </div>
                                {this.state.showLevelDetail[2] && (
                                    <div className="mt-2">
                                        <p className="mxt--small">
                                            {gettext("La Diversité, l'Équité et l’Inclusion est un thème qui vous intéresse, voire vous plaît et vous en comprenez les enjeux.")}
                                            <br/><br/>
                                            {gettext("Vous avez de bonnes connaissances sur les sujets de Diversité, d'Équité et d’Inclusion et ce sont des sujets complexes et aux dimensions multiples. Nous recommandons de continuer à challenger vos connaissances et à garder de la curiosité sur l’ensemble des thématiques. Valorisez la diversité et l’inclusion dans votre métier et vos actions.")}
                                            <br/><br/>
                                            {gettext("Vos maîtres mots pour la suite : ")}
                                            <b>{gettext("approfondissement")}</b>
                                            {gettext(" et ")}
                                            <b>{gettext("persévérance")}</b>
                                            {gettext(".")}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div>
                                <div className="pt-1 pb-2 d-flex justify-content-between" style={{ borderBottom: `2px solid ${getColors('repartition_list', [1])[0]}`, cursor: 'pointer' }} onClick={() => this.handleLevelToggle(3)}>
                                    <h3>{gettext("Niveau 4")}</h3>
                                    <div className="d-flex align-items-center px-2">
                                        <img
                                            style={{
                                                transition: 'transform 0.3s',
                                                transform: !this.state.showLevelDetail[3] ? 'rotate(0deg)' : 'rotate(180deg)',
                                                width: '15px',
                                            }}
                                            src={'/static/icon/chevron-down.svg'}
                                            alt="v"
                                        />
                                    </div>
                                </div>
                                {this.state.showLevelDetail[3] && (
                                    <div className="mt-2">
                                        <p className="mxt--small">
                                            {gettext("Vous êtes pleinement investi.e sur le sujet de la Diversité, de l'Équité et de l’Inclusion et vous comprenez que le sujet est dense et complexe.")}
                                            <br/><br/>
                                            {gettext("Vous avez une très bonne connaissance des sujets de Diversité d'Équité et d'Inclusion ! Continuez d’apprendre, restez humble et portez le sujet à tous les niveaux possibles. La suite se construira avec vous : n'hésitez pas à être porte-parole de ces sujets dans votre métier et à valoriser la notion de responsabilité au recrutement.")}
                                            <br/><br/>
                                            {gettext("Vos maîtres mots pour la suite : ")}
                                            <b>{gettext("innovation")}</b>
                                            {gettext(" et ")}
                                            <b>{gettext("pérennité")}</b>
                                            {gettext(".")}
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="h-100 d-flex justify-content-center" style={{ width: '33%'}}>
                            <div className="h-100" style={{ width: '80px' }}>
                                {data.map((value, index) => ({value, index})).filter(item => item.value > 0).map((item, index, filtered_data) => {
                                    return (
                                        <div
                                            key={item.index}
                                            className={`profile_repartition_bar${index == 0 ? '_first' : index == filtered_data.length - 1 ? '_last' : ''}`}
                                            style={{ width: '100%', height: `${item.value}%`, backgroundColor: `${getColors('repartition_list', [4 - item.index])[0]}` }}
                                        >
                                            {item.value}%
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="ms-3 d-flex flex-column gap-3">
                                {data.map((_, index) => {
                                    return (
                                        <div className="d-flex align-items-center">
                                            <div className="mx-2" style={{ width: '15px', height: '15px', borderRadius: '50%', backgroundColor: `${getColors('repartition_list', [4 - index])[0]}`, }}></div>
                                            <p className="mxt--xs m-0"><b>{gettext(`NIVEAU ${index + 1}`)}</b></p>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

export default DisplayProfileRepartition;
