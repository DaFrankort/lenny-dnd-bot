from embeds.grouproll import GroupRollContainerView

# TODO: Create a InitiativeRollModal class to inherit GroupRollRollModal
# this class would hold the initiative logic, such as storing previous initiative values

class InitiativeContainerView(GroupRollContainerView):
    def __init__(self):
        super().__init__(reason="initiative")
