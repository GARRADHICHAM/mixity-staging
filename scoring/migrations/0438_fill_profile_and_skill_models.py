from django.db import migrations


def new_categories(apps, schema_editor):
    Skill = apps.get_model("scoring", "Skill")
    Profile = apps.get_model("scoring", "Profile")

    Skill.objects.create(
        name="Prise de recul",
        slug="perspective",
        order=0,
        color="#ffcfc9",
    )
    Skill.objects.create(
        name="Écoute",
        slug="listening",
        order=1,
        color="#ffcfc9",
    )
    Skill.objects.create(
        name="Curiosité",
        slug="curiosity",
        order=2,
        color="#ffcfc9",
    )
    Skill.objects.create(
        name="Organisation",
        slug="organization",
        order=3,
        color="#ffcfc9",
    )
    Profile.objects.create(
        slug="committed",
        order=0,
        name="engagé",
        name_fr="engagé",
        name_en="committed",
        name_es="comprometido",
        strenght="La diversité, l'équité et l’inclusion sont des thèmes qui vous intéressent - voire vous plaisent - et vous en comprenez les enjeux.",
        strenght_fr="La diversité, l'équité et l’inclusion sont des thèmes qui vous intéressent - voire vous plaisent - et vous en comprenez les enjeux.",
        strenght_en="Diversity, equity and inclusion are issues that interest you - and even appeal to you - and you understand what's at stake.",
        strenght_es="La diversidad, la equidad y la inclusión son temas que le interesan -e incluso le atraen- y entiende lo que está en juego.",
        improvement="Vous avez de bonnes connaissances sur ces thématiques complexes aux dimensions multiples. Nous vous recommandons de continuer à challenger vos connaissances et à garder de la curiosité sur l’ensemble des sujets de DE&I. Valorisez la diversité et l’inclusion dans votre métier et vos actions.",
        improvement_fr="Vous avez de bonnes connaissances sur ces thématiques complexes aux dimensions multiples. Nous vous recommandons de continuer à challenger vos connaissances et à garder de la curiosité sur l’ensemble des sujets de DE&I. Valorisez la diversité et l’inclusion dans votre métier et vos actions.",
        improvement_en="You have a good knowledge of these complex, multi-dimensional issues. We recommend that you continue to challenge your knowledge and remain curious about all DE&I topics. Promote diversity and inclusion in your job and your actions.",
        improvement_es="Usted tiene un buen conocimiento de estas cuestiones complejas y multidimensionales. Le recomendamos que siga desafiando sus conocimientos y mantenga la curiosidad por todos los temas de DE&I. Promueva la diversidad y la inclusión en su trabajo y en sus acciones.",
        type="approfondissement et persévérance",
        type_fr="approfondissement et persévérance",
        type_en="deepening and perseverance",
        type_es="profundización y perseverancia",
    )
    Profile.objects.create(
        slug="inclusive",
        name="inclusif",
        order=1,
        name_fr="inclusif",
        name_en="inclusive",
        name_es="inclusivo",
        strenght="Vous êtes pleinement investi (f/h/nb) sur les sujets de diversité, d’équité et d’inclusion et comprenez que le sujet est dense et complexe.",
        strenght_fr="Vous êtes pleinement investi (f/h/nb) sur les sujets de diversité, d’équité et d’inclusion et comprenez que le sujet est dense et complexe.",
        strenght_en="You are fully committed (f/h/nb) to diversity, equity and inclusion issues and understand that the subject is dense and complex.",
        strenght_es="Usted está plenamente comprometido (f/h/nb) con las cuestiones de diversidad, equidad e inclusión y comprende que el tema es denso y complejo.",
        improvement="Vous avez une très bonne connaissance des sujets de DE&I ! Continuez d’apprendre, restez humble et portez ces sujets à tous les niveaux possibles. La suite se construira avec vous : n'hésitez pas à être porte-parole de ces thématiques dans votre profession et à valoriser ces notions et leur importance dans votre activité et auprès de vos collaborateurs (f/h/nb).",
        improvement_fr="Vous avez une très bonne connaissance des sujets de DE&I ! Continuez d’apprendre, restez humble et portez ces sujets à tous les niveaux possibles. La suite se construira avec vous : n'hésitez pas à être porte-parole de ces thématiques dans votre profession et à valoriser ces notions et leur importance dans votre activité et auprès de vos collaborateurs (f/h/nb).",
        improvement_en="You have a very good knowledge of DE&I subjects! Keep learning, stay humble and take these subjects to every possible level. The rest will be built with you: don't hesitate to be a spokesperson for these issues in your profession and to promote these concepts and their importance in your business and among your employees (f/h/nb).",
        improvement_es="¡Tienes muy buenos conocimientos de los temas de DE&I! Sigue aprendiendo, mantén la humildad y lleva estos temas a todos los niveles posibles. El resto se construirá contigo: no dudes en ser portavoz de estos temas en tu profesión y en promover estos conceptos y su importancia en tu empresa y entre tus empleados (f/h/nb).",
        type="innovation et pérennité",
        type_fr="innovation et pérennité",
        type_en="innovation and sustainability",
        type_es="innovación y sostenibilidad",
    )
    Profile.objects.create(
        slug="conventional",
        name="traditionnel",
        order=2,
        name_fr="traditionnel",
        name_en="conventional",
        name_es="tradicional",
        strenght="Vous avez une conscience partielle des enjeux de diversité et d’inclusion et n'êtes pas vraiment engagé (f/h/nb) sur ces sujets.",
        strenght_fr="Vous avez une conscience partielle des enjeux de diversité et d’inclusion et n'êtes pas vraiment engagé (f/h/nb) sur ces sujets.",
        strenght_en="You have a partial awareness of diversity and inclusion issues and are not really committed (f/h/nb) to these subjects.",
        strenght_es="Tiene una conciencia parcial de las cuestiones de diversidad e inclusión y no está realmente comprometido (f/h/nb) con estos temas.",
        improvement="Nous vous recommandons de vous renseigner sur l’importance d'une politique inclusive dans votre activité et à vous pencher sur les actions à mettre en place pour garantir une telle démarche. Quand vous vous sentirez prêt (f/h/nb), réfléchissez sur vos possibles biais, vos comportements, mais aussi et surtout comment ils impactent votre mission et organisation.",
        improvement_fr="Nous vous recommandons de vous renseigner sur l’importance d'une politique inclusive dans votre activité et à vous pencher sur les actions à mettre en place pour garantir une telle démarche. Quand vous vous sentirez prêt (f/h/nb), réfléchissez sur vos possibles biais, vos comportements, mais aussi et surtout comment ils impactent votre mission et organisation.",
        improvement_en="We recommend that you find out about the importance of an inclusive policy in your business and look at the actions you need to put in place to ensure this happens. When you feel ready (f/h/nb), think about your possible biases, your behaviours, but also and above all how they impact your mission and organisation.",
        improvement_es="Le recomendamos que se informe sobre la importancia de una política inclusiva en su empresa y estudie las medidas que debe poner en marcha para garantizar que así sea. Cuando te sientas preparado (f/h/nb), piensa en tus posibles prejuicios, en tus comportamientos, pero también y sobre todo en cómo afectan a tu misión y a tu organización.",
        type="curiosité et ouverture",
        type_fr="curiosité et ouverture",
        type_en="curiosity and open-mindedness",
        type_es="curiosidad y apertura",
    )
    Profile.objects.create(
        slug="in_transition",
        name="en transition",
        order=3,
        name_fr="en transition",
        name_en="in transition",
        name_es="en transición",
        strenght="Vous avez conscience de l’enjeu stratégique que représentent les sujets de diversité, d’équité et d’inclusion.",
        strenght_fr="Vous avez conscience de l’enjeu stratégique que représentent les sujets de diversité, d’équité et d’inclusion.",
        strenght_en="You are aware of the strategic importance of diversity, equity and inclusion.",
        strenght_es="Es consciente de la importancia estratégica de la diversidad, la equidad y la inclusión.",
        improvement="Vous sentez-vous équipé et motivé (f/h/nb) pour discuter et agir auprès de vos collègues, pour questionner les comportements et processus existants, y compris les vôtres ? N’hésitez pas à aller au-delà de la stratégie DE&I de votre entreprise et à vous mettre en situation d'apprentissage sur ces questions, même si cela peut être inconfortable.",
        improvement_fr="Vous sentez-vous équipé et motivé (f/h/nb) pour discuter et agir auprès de vos collègues, pour questionner les comportements et processus existants, y compris les vôtres ? N’hésitez pas à aller au-delà de la stratégie DE&I de votre entreprise et à vous mettre en situation d'apprentissage sur ces questions, même si cela peut être inconfortable.",
        improvement_en="Do you feel equipped and motivated (f/h/nb) to discuss and act with your colleagues, to question existing behaviours and processes, including your own? Don't hesitate to go beyond your company's DE&I strategy and put yourself in a position to learn about these issues, even if it may be uncomfortable.",
        improvement_es="¿Se siente equipado y motivado (f/h/nb) para debatir y actuar con sus colegas, para cuestionar los comportamientos y procesos existentes, incluidos los suyos propios? No dude en ir más allá de la estrategia de DE&I de su empresa y póngase en situación de aprender sobre estas cuestiones, aunque pueda resultar incómodo.",
        type="introspection et engagement",
        type_fr="introspection et engagement",
        type_en="introspection and commitment",
        type_es="introspección y compromiso",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0437_auto_20240829_1119"),
    ]

    operations = [
        migrations.RunPython(new_categories, lambda x, y: None),
    ]
