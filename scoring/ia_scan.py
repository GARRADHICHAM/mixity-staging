from django.utils.translation import ugettext_lazy as _, get_language
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q, F, QuerySet

import json

from scoring.models import (
    Evaluation,
    Answer,
    IAScanAnalysis,
    IAScanAnalysisElement,
    Category,
    SCAN_CATEGORIES_SLUGS,
)

from openai import OpenAI


class IAScan:
    _instance = None

    def do_scan_analysis(self, eval_id, scan_collaborator) -> dict:
        if not settings.OPEN_AI_API_KEY:
            return {"status": "error", "message": "Missing API KEY"}
        client = OpenAI(
            api_key=settings.OPEN_AI_API_KEY,
        )

        evaluation = get_object_or_404(Evaluation, pk=eval_id)

        lang = get_language()
        samples = [
            _(
                """
                    Notions générales
                    Points forts :
                    Vous avez une bonne connaissance des aspects juridiques de votre métier.
                    Vous avez pleinement conscience que la majorité des handicaps ne sont pas de naissance.

                    Axes d'amélioration :
                    Vous ne savez pas encore faire clairement la différence entre stéréotypes, préjugés et discriminations.

                    Objectifs :
                    Nous vous conseillons de renforcer vos connaissances théoriques, en particulier sur les stéréotypes et préjugés. Cela vous aidera à mieux les identifier, mais aussi à mieux limiter certains de vos propres biais cognitifs.

                    PRATIQUES PROFESSIONNELLES
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.
                    Vous savez présenter une posture professionnelle inclusive en interrogeant les besoins spécifiques des candidats (f/h/nb) sur un poste, et en adaptant leur intégration en fonction de cela.

                    Axes d'amélioration :

                    Objectifs :


                    Biais cognitifs
                    Points forts :
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement et connaissez l'existence interne de dispositifs pour y faire face.
                    Vous avez pleinement conscience que les loisirs personnels ne définissent et ne comblent en aucun cas le niveau de compétences d'un candidat (f/h/nb). Vous savez alors rester concentrée exclusivement sur ses compétences.
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Vous n'avez pas encore pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées ou motivées.
                    Vous pouvez être disposée, sans vous en rendre compte, à juger plus sévèrement un candidat (f/h/nb) arrivé en retard à un entretien, en dépit de ses compétences objectives.

                    Objectifs :
                    Nous vous conseillons d'interroger votre rapport aux offres d'emploi en privilégiant, lorsque cela est possible, davantage les motivations d'un candidat (f/h/nb) plutôt que ses compétences. Les compétences s'acquièrent plus facilement que la motivation. Vous pouvez aussi interroger l'intérêt de n'indiquer que quelques compétences essentielles plutôt qu'un grand nombre de compétences. Cela pourrait freiner des personnes à postuler.
                    Nous vous conseillons de veiller à toujours prendre un temps de recul dans vos processus d'analyse des candidats (f/h/nb) pour éviter d'être biaisée dans vos décisions. Cela est par exemple le cas pour ceux arrivant en retard. Un retard, dans l'absolu, ne dit rien du niveau de compétences ni de la posture d'une personne.

                    Communication
                    Points forts :
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.
                    Vous savez être à l'écoute et conseiller un collaborateur (f/h/nb) qui vous sollicite sur des enjeux personnels lorsque cela est nécessaire.
                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :

                    Objectifs :


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.
                    Vous savez être à l'écoute et soutenir les personnes souffrant de harcèlement au travail, tout en respectant leur consentement avant d’alerter les parties compétentes.
                    
                    Vous avez conscience de la nécessité de vous former continuellement sur ces enjeux de diversité et inclusion.

                    Axes d'amélioration :
                    Même si vous vous tenez informée sur les sujets de DE&I pour vos activités professionnelles, vous pourriez diversifier les ressources utilisées et vous focaliser sur des ressources plus solides scientifiquement.

                    Objectifs :
                    Nous vous conseillons de poursuivre votre investissement en faveur de la DE&I tout en envisageant d'actualiser davantage vos connaissances à travers des ressources plus diversifiées et rigoureuses.
                  
                """
            ),
            _(
                """
                    Notions générales
                    Points forts :
                    Vous avez une bonne connaissance des aspects juridiques de votre métier.
 
                    Vous avez pleinement conscience que la majorité des handicaps ne sont pas de naissance.

                    Axes d'amélioration :
                    Vous ne savez pas encore faire clairement la différence entre stéréotypes, préjugés et discriminations. Par ailleurs, vous n'avez pas connaissance non plus de ce que représente une discrimination indirecte et la façon dont elles pourraient se manifester dans vos activités.
 
                    Vous n'avez pas pleinement conscience de ce que peut impliquer la façon dont sont rédigées les offres d'emploi sur la motivation des personnes à candidater.

                    Objectifs :
                    Nous vous conseillons de renforcer vos connaissances théoriques, en particulier sur les stéréotypes, préjugés et discriminations indirectes. Cela vous aidera à mieux les identifier à travers vos dispositifs de recrutement ou d'intégration, mais aussi à mieux limiter certains de vos propres biais cognitifs.


                    Pratique professionnelle
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats  (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.
 
                    Vous savez présenter une posture professionnelle inclusive en interrogeant les besoins spécifiques des candidats  (f/h/nb) sur un poste, et en adaptant leur intégration en fonction de cela.

                    Axes d'amélioration :
                    En dépit de nombreuses bonnes réponses sur des mises en situation pour départager des candidats (f/h/nb) , vous n'avez pas su identifier convenablement les pratiques qui permettent d'effectuer un entretien plus inclusif en mentionnant l'utilité des questions personnalisées et des fiches récapitulatives.

                    Objectifs :
                    Nous vous conseillons de poursuivre vos efforts pour veiller à limiter les biais et actualiser vos connaissances sur les pratiques inclusives de votre métier. De façon globale, nous vous suggérons de standardiser vos entretiens pour rester focalisée sur les compétences et toujours vous demander comment ne pas influencer un collègue dans son analyse d'un candidat (f/h/nb). Par exemple, les fiches récapitulatives rédigées peuvent influencer vos collègues dans leurs propres analyses.


                    Biais cognitifs
                    Points forts :
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement. Par ailleurs, vous présentez une certaine habilité à les identifier.
 
                    Vous avez pleinement conscience que les loisirs personnels ne définissent et ne comblent en aucun cas le niveau de compétences d'un candidat (f/h/nb). Vous savez alors rester concentrée exclusivement sur ses compétences.
 
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Vous présentez certaines difficultés à identifier convenablement les pratiques qui permettent de recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Vous n'avez pas encore pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées ou motivées.
 
                    Vous pouvez être disposée, sans vous en rendre compte, à juger plus sévèrement un candidat (f/h/nb) arrivé en retard à un entretien, en dépit de ses compétences objectives.

                    Objectifs :
                    En dépit de votre connaissance des biais cognitifs, nous vous conseillons de rester focalisée sur les dispositifs existants pour y faire face plutôt que sur votre propre confiance à les gérer. Il existe de nombreux biais qui nous impactent sans que nous nous en rendions compte. Avoir connaissance des bonnes pratiques est alors essentiel. Vous pouvez, par exemple, vous informer sur les bonnes pratiques pour recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Nous vous conseillons d'interroger votre rapport aux offres d'emploi en privilégiant, lorsque cela est possible, davantage les motivations d'un candidat (f/h/nb) plutôt que ses compétences. Les compétences s'acquièrent plus facilement que la motivation. Vous pouvez aussi interroger l'intérêt de n'indiquer que quelques compétences essentielles plutôt qu'un grand nombre de compétences. Cela pourrait freiner des personnes à postuler.
 
                    Nous vous conseillons de continuer à toujours prendre un temps de recul dans vos processus d'analyse des candidats (f/h/nb) pour éviter d'être biaisée dans vos décisions. Cela est par exemple le cas pour ceux arrivant en retard. Un retard, dans l'absolu, ne dit rien du niveau de compétences ni de la posture d'une personne.


                    Communication
                    Points forts :
                    Vous savez pertinemment garder une posture professionnelle sans porter de jugements hâtifs sur un candidat  (f/h/nb) malgré les rumeurs.
 
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.
 
                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :
                    Vous ne présentez pas une posture inclusive sur les sujets de transition de genre en considérant qu'ils n'ont rien à faire sur le lieu de travail.

                    Objectifs :
                    Nous vous conseillons de garder une posture ouverte et inclusive sur tous les sujets, quels qu'ils soient, notamment sur les questions de transitions de genre. Bien que ce ne soient pas des sujets habituels, dès lors qu'un collaborateur (f/h/nb) aborde le sujet, c'est qu'il en ressent le besoin et vous estime compétente pour être à son écoute. Il en va du bien-être de la personne mais aussi, plus largement, de la culture et de la posture de l'entreprise.


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.
 
                    Vous vous tenez informée des questions de DE&I en rapport avec votre activité au travers de ressources diversifiées. Par ailleurs, vous utilisez aussi des ressources solides telles que les livres et/ou les publications scientifiques.
 
                    Vous savez être à l'écoute et soutenir les personnes souffrant de harcèlement au travail, tout en respectant leur consentement avant d’alerter les parties compétentes.

                    Axes d'amélioration :
                    Actuellement, vous ne faites pas encore partie d'un groupe de réflexion ou d'un réseau dédié aux sujets liés à la DE&I.

                    Objectifs :
                    Envisagez la possibilité d'intégrer un groupe de réflexion ou un réseau dédié aux sujets liés à la DE&I, notamment pour valoriser d'autant plus vos idées que vous savez partager avec les personnes responsables de ces thématiques.
                  
                """
            ),
            _(
                """
                    Notions générales
                    Points forts :
                    Vous maîtrisez parfaitement les aspects juridiques de votre métier.

                    Vous avez pleinement conscience que la majorité des handicaps ne sont pas de naissance.

                    Axes d'amélioration :
                    Vous ne savez pas encore faire clairement la différence entre stéréotypes et préjugés.

                    Objectifs :
                    Nous vous conseillons de renforcer vos connaissances théoriques sur les stéréotypes et préjugés pour mieux identifier leur émergence dans vos pratiques professionnelles. 


                    Pratique professionnelle
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats  (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.
 
                    Vous savez présenter une posture professionnelle inclusive en interrogeant les besoins spécifiques des candidats  (f/h/nb) sur un poste, et en adaptant leur intégration en fonction de cela.

                    Axes d'amélioration :
                    En dépit de nombreuses bonnes réponses sur des mises en situation pour départager des candidats (f/h/nb), vous n'avez pas su totalement identifier les pratiques inclusives pour une procédure de sélection ou afin d'attirer davantage de femmes sur un recrutement pour un poste traditionnellement masculin.

                    Objectifs :
                    Nous vous conseillons de continuer à vous informer sur les pratiques inclusives, d'une part dans le sourcing pour mieux diffuser vos offres aux populations cibles, mais aussi dans les processus d'entretien et de sélection.


                    Biais cognitifs
                    Points forts :
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement. Par ailleurs, vous présentez une certaine habilité à les identifier.
 
                    Vous avez pleinement conscience que les loisirs personnels ne définissent et ne comblent en aucun cas le niveau de compétences d'un candidat (f/h/nb). Vous savez alors rester concentrée exclusivement sur ses compétences.
 
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Vous présentez certaines difficultés à identifier convenablement les pratiques qui permettent de recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Vous n'avez pas encore pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées ou motivées.
 
                    Vous pouvez être disposée, sans vous en rendre compte, à juger plus sévèrement un candidat (f/h/nb) arrivé en retard à un entretien, en dépit de ses compétences objectives.

                    Objectifs :
                    En dépit de votre connaissance des biais cognitifs, nous vous conseillons de rester focalisée sur les dispositifs existants pour y faire face plutôt que sur votre propre confiance à les gérer. Il existe de nombreux biais qui nous impactent sans que nous nous en rendions compte. Avoir connaissance des bonnes pratiques est alors essentiel. Vous pouvez, par exemple, vous informer sur les bonnes pratiques pour recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Nous vous conseillons d'interroger votre rapport aux offres d'emploi en privilégiant, lorsque cela est possible, davantage les motivations d'un candidat (f/h/nb) plutôt que ses compétences. Les compétences s'acquièrent plus facilement que la motivation. Vous pouvez aussi interroger l'intérêt de n'indiquer que quelques compétences essentielles plutôt qu'un grand nombre de compétences. Cela pourrait freiner des personnes à postuler.
 
                    Nous vous conseillons de continuer à toujours prendre un temps de recul dans vos processus d'analyse des candidats (f/h/nb) pour éviter d'être biaisée dans vos décisions. Cela est par exemple le cas pour ceux arrivant en retard. Un retard, dans l'absolu, ne dit rien du niveau de compétences ni de la posture d'une personne.


                    Communication
                    Points forts :
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.

                    Vous savez être à l'écoute et conseiller un collaborateur (f/h/nb) qui vous sollicite sur des enjeux personnels lorsque cela est nécessaire.

                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :

                    Objectifs :


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.

                    Vous savez être à l'écoute et soutenir les personnes souffrant de harcèlement au travail, tout en respectant leur consentement avant d’alerter les parties compétentes.

                    Axes d'amélioration :
                    Même si vous vous tenez informée sur les sujets de DE&I pour vos activités professionnelles, vous pourriez diversifier les ressources utilisées et vous focaliser sur des ressources plus solides scientifiquement.

                    Objectifs :
                    Nous vous conseillons de poursuivre votre investissement en faveur de la DE&I tout en envisageant d'actualiser davantage vos connaissances à travers des ressources plus diversifiées et rigoureuses.
                  
                """
            ),
            _(
                """
                    Notions générales
                    Points forts :
                    Vous avez une bonne connaissance des aspects juridiques de votre métier.
 
                    Vous avez pleinement conscience que la majorité des handicaps ne sont pas de naissance.
 
                    Vous savez faire la différence entre stéréotypes, préjugés et discriminations. Cela vous assure de mieux identifier les manifestations de ces derniers dans vos pratiques pour mieux y faire face.

                    Axes d'amélioration :

                    Objectifs :


                    Pratique professionnelle
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.
 
                    Vous savez présenter une posture professionnelle inclusive en interrogeant les besoins spécifiques des candidats (f/h/nb) sur un poste, et en adaptant leur intégration en fonction de cela.

                    Axes d'amélioration :
                    En dépit de nombreuses bonnes réponses sur des mises en situation pour départager des candidats (f/h/nb), vous n'avez pas su totalement identifier les pratiques inclusives pour une procédure de sélection.

                    Objectifs :
                    Nous vous conseillons de continuer à vous informer sur les pratiques inclusives, notamment sur les dispositifs d'analyse et de sélection. Ceux-ci doivent toujours être standardisés et conçus pour minimiser l'influence mutuelle pouvant survenir entre collègues. N'hésitez pas non plus à multiplier ces dispositifs pour réduire d'autant plus ces risques.


                    Biais cognitifs
                    Points forts :
                    Vous avez pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées, ni des personnes motivées.
 
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement et connaissez l'existence interne de dispositifs pour y faire face.
 
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Vous présentez certaines difficultés à identifier convenablement les pratiques qui permettent de recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Sur une question, en dépit du manque de compétences d'un candidat (f/h/nb), vous avez appréhendé ce dernier différemment pour sa passion du basket.
 
                    Vous pouvez être disposée, sans vous en rendre compte, à juger plus sévèrement un candidat (f/h/nb) arrivé en retard à un entretien, en dépit de ses compétences objectives.

                    Objectifs :
                    En dépit de votre connaissance des biais cognitifs, vous restez fortement sujette à ces derniers. Nous vous conseillons de rester focalisée sur les dispositifs existants pour y faire face et exclusivement sur le niveau de compétences des candidats (f/h/nb) plutôt que sur leurs loisirs personnels. Il existe de nombreux biais qui nous impactent sans que nous nous en rendions compte. Avoir connaissance des bonnes pratiques est alors essentiel. Vous pouvez, par exemple, vous informer sur les bonnes pratiques pour recruter dans un bassin diversifié de candidats (f/h/nb).
 
                    Nous vous conseillons de continuer à toujours prendre un temps de recul dans vos processus d'analyse des candidats (f/h/nb) pour éviter d'être biaisée dans vos décisions. Cela est par exemple le cas pour ceux arrivant en retard. Un retard, dans l'absolu, ne dit rien du niveau de compétences ni de la posture d'une personne.


                    Communication
                    Points forts :
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.
 
                    Vous savez être à l'écoute et conseiller un collaborateur (f/h/nb) qui vous sollicite sur des enjeux personnels lorsque cela est nécessaire.
 
                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :

                    Objectifs :


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.
 
                    Vous savez être à l'écoute et soutenir les personnes souffrant de harcèlement au travail, tout en respectant leur consentement avant d’alerter les parties compétentes. 
 
                    Vous avez déjà participé, il y a moins d'un an, à une sensibilisation en faveur de la diversité et l'inclusion sur la base du volontariat.
 
                    Vous vous tenez informée des questions de DE&I en rapport avec votre activité au travers de ressources diversifiées. Par ailleurs, vous utilisez aussi des ressources solides telles que les livres et/ou les publications scientifiques.

                    Axes d'amélioration :

                    Objectifs :
                  
                """
            ),
            _(
                """
                    Notions générales
                    Points forts :
                    Vous avez une bonne connaissance des aspects juridiques de votre métier.
 
                    Vous avez pleinement conscience que la majorité des handicaps ne sont pas de naissance.
 
                    Vous savez faire la différence entre stéréotypes, préjugés et discriminations. Cela vous assure de mieux identifier ces derniers dans vos pratiques professionnelles, et ainsi de mieux pouvoir y faire face.

                    Axes d'amélioration :

                    Objectifs :


                    Pratique professionnelle
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.
 
                    Vous savez présenter une posture professionnelle inclusive en interrogeant les besoins spécifiques des candidats (f/h/nb) sur un poste, et en adaptant leur intégration en fonction de cela.
 
                    Vous avez su pertinemment identifier les pratiques les plus inclusives pour réaliser des phases d'entretien et de sélection des candidats (f/h/nb).

                    Axes d'amélioration :

                    Objectifs :


                    Biais cognitifs
                    Points forts :
                    Vous avez pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées, ni des personnes motivées.
 
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement et connaissez l'existence interne de dispositifs pour y faire face. Par ailleurs, vous ne tombez pas dans le piège de juger des compétences d'un candidat (f/h/nb) pour un retard à l'entretien.
 
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Sur une question, en dépit du manque de compétences d'un candidat (f/h/nb) pour le poste, vous avez estimé pouvoir appréhender différemment ce dernier pour sa passion du basket.
 
                    Sur une question liée à l'apparence physique d'un candidat (f/h/nb), vous avez préféré aborder ce « problème » perçu par votre collègue autour d'un temps d'échange commun plutôt que de rassurer ce dernier sur les compétences de la personne.

                    Objectifs :
                    En dépit de votre connaissance des biais cognitifs, nous vous conseillons de rester focalisée sur les dispositifs existants pour y faire face et exclusivement sur le niveau de compétences des candidats (f/h/nb) plutôt que sur leurs loisirs personnels. Ces derniers ne constituent en rien une preuve de compétences. Privilégiez toujours des mises en situation standardisées pour comparer objectivement les personnes.
 
                    Nous vous conseillons de veiller à ce que l'apparence physique ne soit pas un critère qui privilégie un candidat (f/h/nb) plutôt qu'un autre, au-delà des compétences. Dans le cas où aucune obligation ne stipule la nécessité d'une tenue vestimentaire adaptée, rassurez plutôt vos collègues sur les compétences de la personne. Être inclusif stipule que l'organisation s'adapte aussi aux personnes et à leur singularité.


                    Communication
                    Points forts :
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.
 
                    Vous savez être à l'écoute et conseiller un collaborateur (f/h/nb) qui vous sollicite sur des enjeux personnels lorsque cela est nécessaire.
 
                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :

                    Objectifs :


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.
 
                    Vous savez être à l'écoute et soutenir les personnes souffrant de harcèlement au travail, tout en respectant leur consentement avant d’alerter les parties compétentes. 
 
                    Vous avez déjà participé, il y a moins d'un an, à une sensibilisation en faveur de la diversité et l'inclusion sur la base du volontariat.
 
                    Vous vous tenez informée des questions de DE&I en rapport avec votre activité au travers de ressources diversifiées. Par ailleurs, vous utilisez aussi des ressources solides telles que les livres et/ou les publications scientifiques.

                    Axes d'amélioration :

                    Objectifs :
                  
                """
            ),
            _(
                """
                    Notions générales
                    Points forts :
                    Dans l'ensemble, vous avez une bonne connaissance des aspects juridiques de votre métier.
 
                    Vous savez faire la différence entre stéréotypes, préjugés et discriminations. Cela vous assure de mieux identifier ces derniers dans vos pratiques professionnelles, et ainsi de mieux pouvoir y faire face.

                    Axes d'amélioration :
                    En dépit de quelques bonnes réponses, vous semblez présenter quelques lacunes au niveau juridique (questions légales, discrimination indirecte, conséquences légales d'une discrimination à l'embauche).

                    Objectifs :
                    Nous vous conseillons d'approfondir vos connaissances juridiques afin de vous assurer d'être conforme dans vos processus de recrutement, tout en structurant des pratiques équitables qui favorisent la diversité et l’inclusion.


                    Pratique professionnelle
                    Points forts :
                    Vous avez pleinement conscience des solutions qui s'offrent à vous pour traiter et départager des candidats (f/h/nb) de façon impartiale, notamment en vous focalisant exclusivement sur leurs compétences plutôt que sur d'autres critères non pertinents et/ou illégaux.

                    Axes d'amélioration :
                    En dépit de quelques bonnes réponses, vous semblez présenter quelques lacunes dans vos connaissances sur les bonnes pratiques pour favoriser l'intégration d'un nouveau collaborateur (f/h/nb).
 
                    En dépit de plusieurs bonnes réponses sur des mises en situation pour départager des candidats (f/h/nb), vous n'avez pas su totalement identifier les pratiques inclusives pour une procédure de sélection.

                    Objectifs :
                    Nous vous conseillons d'approfondir vos connaissances sur les bonnes pratiques pour intégrer un nouveau collaborateur (f/h/nb). Le tutorat, l'aménagement de poste, le suivi régulier sont quelques exemples de bonnes pratiques. Le mieux est de multiplier ces dernières pour assurer une meilleure qualité de vie aux personnes nouvellement arrivées. Cela facilitera leur bien-être au travail et leur motivation.
 
                    Nous vous conseillons de continuer à vous informer sur les pratiques inclusives, notamment sur les dispositifs d'analyse et de sélection. Ceux-ci doivent toujours être standardisés et conçus pour minimiser l'influence mutuelle pouvant survenir entre collègues. N'hésitez pas non plus à multiplier ces dispositifs pour réduire d'autant plus ces risques.


                    Biais cognitifs
                    Points forts :
                    Vous avez conscience de l'importance des biais cognitifs dans les processus de recrutement et connaissez l'existence interne de dispositifs pour y faire face.
 
                    Vous avez pleinement conscience que les loisirs personnels ne définissent et ne comblent en aucun cas le niveau de compétences d'un candidat (f/h/nb). Vous savez alors rester concentrée exclusivement sur ses compétences.
 
                    Vous présentez une posture professionnelle inclusive lorsqu'il s'agit de déléguer certaines tâches (écoute, disponibilité, bienveillance).

                    Axes d'amélioration :
                    Vous n'avez pas encore pleinement conscience qu'une offre d'emploi avec de nombreuses compétences demandées ne permet pas nécessairement d'obtenir des personnes qualifiées ou motivées.
 
                    Vous pouvez être disposée, sans vous en rendre compte, à juger plus sévèrement un candidat (f/h/nb) arrivé en retard à un entretien, en dépit de ses compétences objectives.

                    Objectifs :
                    Nous vous conseillons d'interroger votre rapport aux offres d'emploi en privilégiant, lorsque cela est possible, davantage les motivations d'un candidat plutôt que ses compétences. Les compétences s'acquièrent plus facilement que la motivation. Vous pouvez aussi interroger l'intérêt de n'indiquer que quelques compétences essentielles plutôt qu'un grand nombre de compétences. Cela pourrait freiner des personnes à postuler.
 
                    Nous vous conseillons de veiller à toujours prendre un temps de recul dans vos processus d'analyse des candidats pour éviter d'être biaisée dans vos décisions. Cela est par exemple le cas pour ceux arrivant en retard. Un retard, dans l'absolu, ne dit rien du niveau de compétences ni de la posture d'une personne.


                    Communication
                    Points forts :
                    Vous savez garder une posture professionnelle qui ne confonde pas vos opinions personnelles et vos obligations professionnelles dans un contexte où vous ne seriez pas d'accord avec la stratégie de votre entreprise.
 
                    Vous savez être à l'écoute et conseiller un collaborateur (f/h/nb) qui vous sollicite sur des enjeux personnels lorsque cela est nécessaire.
 
                    Vous savez adopter une communication inclusive en contexte informel.

                    Axes d'amélioration :

                    Objectifs :


                    Engagement professionel  
                    Points forts :
                    Vous avez pleinement conscience que l'inclusion au travail est essentielle, tant pour le bien-être des collaborateurs (f/h/nb) que pour la performance de l'entreprise. Par ailleurs, vous essayez d'y contribuer du mieux possible dans vos activités professionnelles.
 
                    Vous avez déjà participé, il y a moins d'un an, à une sensibilisation en faveur de la diversité et l'inclusion sur la base du volontariat.
 
                    Vous vous tenez informée des questions de DE&I en rapport avec votre activité au travers de ressources diversifiées. Par ailleurs, vous utilisez aussi des ressources solides telles que les livres et/ou les publications scientifiques.

                    Axes d'amélioration :
                    Dans un contexte de harcèlement, vous signalez immédiatement le comportement aux supérieurs compétents, sans même l'accord de la victime et avant même de la soutenir moralement.

                    Objectifs :
                    Dans un contexte de violences ou de harcèlements, nous vous conseillons d'apprendre à prendre parti de la victime en confrontant l'agresseur si cela est possible, et de toujours soutenir la victime par une posture d'écoute, de bienveillance et d'accompagnement. Par ailleurs, préférez toujours faire remonter la situation avec l'accord de la personne.
                """
            ),
        ]

        str_sample = str(samples)

        categories = ", ".join([cat.name for cat in Category.objects.filter(slug__in=SCAN_CATEGORIES_SLUGS)])

        feedback_types = "Points forts, Axes d'amélioration, Objectifs"

        system_prompt = str(
            f"You will be provided with a data set with each line containing a category, sub-category, question, answer, answer value, maximum possible value and question weight. With this I want you to make an analysis of the answers and the respondent, you need to separate your analysis into 5 categories : {categories}. Each category must be separated into 3 subcategories : {feedback_types}, you must fill the first one but you are not obligated to do the last two if the respondent do not need them. If you fill the 2nd one, you must fill the 3rd one. Please talk to the respondent, with 'you...' but not 'the respondent...'. Write your analysis in a python dict format ({{}} for the json like dictionnary and [] for lists), with the first level of depth being the 5 categories I gave you, the 2nd level being the 3 subcategories I gave you, and the last level being the content in a list of strings. Do not write in md, and do not put carriage returns. At the end of this message, I'll give you a sample analysis containing 6 analysis, take your inspiration from them. The next message will be the data set. Answer only 'OK' if you've understood, and once you've got the data set, I want you to answer only with the analysis please. Also, you must respond and make your analysis in {lang}. The sample is: {str_sample}"
        )

        user_answers = Answer.objects.filter(
            evaluation=evaluation, scan_collaborator=scan_collaborator
        ).select_related(
            "choice", "question", "question__category", "question__subcategory"
        )

        data_set = []

        for answer in user_answers:
            if not answer or not answer.choice:
                continue
            data_set.append(
                {
                    "category": answer.question.category,
                    "sub_category": answer.question.subcategory,
                    "question": answer.question.label,
                    "answer": answer.choice.label,
                    "value": answer.choice.value,
                    "max_value": max(
                        [choice.value for choice in answer.question.choices.all()]
                    ),
                    "question_weight_index": answer.question.weight_index,
                }
            )

        user_prompt = str(data_set)

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                top_p=1,
            )

            if not hasattr(response, "choices") or not response.choices:
                raise ValueError("The response does not contain 'choices' or it is empty.")

            content = response.choices[0].message.content

            if not content:
                raise ValueError("The response message content is empty.")

            result = json.loads(content)

            if not isinstance(result, dict):
                raise ValueError("Parsed result is not in the expected format (dict).")

            queryset = IAScanAnalysis.objects.filter(
                evaluation=evaluation, scan_collaborator=scan_collaborator
            )
            if queryset.exists():
                analysis = queryset.first()
                elements = analysis.ia_scan_analysis_elements.all()
                for element in elements:
                    element.delete()
                analysis.is_validated_by_admin = False
                analysis.save()
            else:
                analysis = IAScanAnalysis.objects.create(
                    evaluation=evaluation,
                    scan_collaborator=scan_collaborator,
                    is_validated_by_admin=False,
                )

            category_slugs = {cat.name: cat.slug for cat in Category.objects.filter(slug__in=SCAN_CATEGORIES_SLUGS)}
            type_slugs = {"Points forts": "strength", "Axes d'amélioration": "weakness", "Objectifs": "aim"}

            for category, values in result.items():
                for type, contents in values.items():
                    for content in contents:
                        element = IAScanAnalysisElement.objects.create(
                            analysis=analysis,
                            category=Category.objects.get(slug=category_slugs[category]),
                            type=type_slugs[type],
                            content=content,
                        )

            return {"status": "success", "message": "The analysis was successfully done"}

        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Failed to decode JSON: {e}"}
        
        except AttributeError as e:
            return {"status": "error", "message": f"Unexpected response structure: {e}"}

        except ValueError as e:
            return {"status": "error", "message": f"Response validation error: {e}"}

        except client.APIError as e:
            return {"status": "error", "message": f"API error: {e}"}

        except Exception as e:
            return {"status": "error", "message": f"An error occured: {e}"}


    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = IAScan()
        return cls._instance
