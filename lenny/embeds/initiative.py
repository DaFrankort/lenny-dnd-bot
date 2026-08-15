from embeds.grouproll import GroupRollContainerView


class InitiativeContainerView(GroupRollContainerView):
    def __init__(self):
        super().__init__(reason="initiative")
