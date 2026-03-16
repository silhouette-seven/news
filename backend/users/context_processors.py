from users.models import UserTagScore


def user_tags_processor(request):
    """Inject the user's top tags into every template context for the header sub-nav."""
    if request.user.is_authenticated:
        top_tags = UserTagScore.get_top_tags(request.user, limit=10)
        return {'user_top_tags': top_tags}
    return {'user_top_tags': []}
