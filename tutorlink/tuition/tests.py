from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .matching import calculate_match
from .models import Application, Comment, SavedPost, TuitionPost

User = get_user_model()

POST_DATA = {
    "subject": "Mathematics",
    "class_level": "Class 10",
    "budget": "6,000 – 8,000",
    "post_type": "NEED",
    "division": "Dhaka",
    "district": "Dhaka",
    "area": "Dhanmondi",
    "preferred_days": ["Sat", "Mon", "Wed"],
    "time_slot": "5:00 PM – 7:00 PM",
    "teaching_mode": "ONLINE",
    "description": "I am in Class 10 (SSC candidate). Need help in Algebra and Geometry.",
}


def make_user(name, role, verified=True):
    return User.objects.create_user(
        username=name, password="pw12345!", role=role, first_name=name.title(),
        area="Dhanmondi", district="Dhaka", division="Dhaka", is_verified=verified,
    )


class TuitionFlowTests(TestCase):
    def setUp(self):
        self.student = make_user("ayesha", "STUDENT")
        self.tutor = make_user("tanvir", "TUTOR")

    def publish(self, **over):
        self.client.force_login(self.student)
        return self.client.post(reverse("tuition:create_post"), {**POST_DATA, "publish": "1", **over})

    # ---- screen 09 ------------------------------------------------------
    def test_create_page_renders_for_student(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("tuition:create_post")), "Create Tuition Post")

    def test_tutor_cannot_create(self):
        self.client.force_login(self.tutor)
        r = self.client.get(reverse("tuition:create_post"))
        self.assertRedirects(r, reverse("role_dashboard"), fetch_redirect_response=False)

    def test_publish_and_draft(self):
        r = self.publish()
        post = TuitionPost.objects.get()
        self.assertRedirects(r, post.get_absolute_url())
        self.assertEqual((post.status, post.budget_min, post.budget_max), ("OPEN", 6000, 8000))
        self.assertEqual(post.preferred_days, "Sat,Mon,Wed")

        self.client.post(reverse("tuition:create_post"), {**POST_DATA, "save_draft": "1"})
        self.assertEqual(TuitionPost.objects.filter(status="DRAFT").count(), 1)

    def test_validation_errors(self):
        r = self.publish(budget="abc", area="Atlantis", description="short")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(TuitionPost.objects.count(), 0)
        self.assertContains(r, "Enter a budget")

    def test_single_number_budget(self):
        self.publish(budget="5500")
        post = TuitionPost.objects.get()
        self.assertEqual((post.budget_min, post.budget_max), (5500, 5500))

    # ---- screen 10 ------------------------------------------------------
    def test_find_tuition_lists_open_posts_only(self):
        self.publish()
        self.client.post(reverse("tuition:create_post"), {**POST_DATA, "save_draft": "1", "subject": "Physics"})
        self.client.force_login(self.tutor)
        r = self.client.get(reverse("tuition:find_tuition"))
        self.assertContains(r, "Mathematics · Class 10")
        self.assertNotContains(r, "Physics · Class 10")
        self.assertContains(r, "1 Tuition Post Found")

    def test_filters(self):
        self.publish()
        self.publish(subject="Physics", budget="9000", teaching_mode="OFFLINE")
        self.client.force_login(self.tutor)
        url = reverse("tuition:find_tuition")
        self.assertContains(self.client.get(url, {"f": 1, "subject": "Physics", "mode": ["OFFLINE"], "open_only": 1,
                                                 "min_budget": 3000, "max_budget": 10000}), "1 Tuition Post Found")
        self.assertContains(self.client.get(url, {"f": 1, "mode": ["ONLINE"], "open_only": 1,
                                                 "min_budget": 3000, "max_budget": 10000}), "1 Tuition Post Found")
        self.assertContains(self.client.get(url, {"f": 1, "max_budget": 4000, "mode": ["ONLINE", "OFFLINE"],
                                                 "open_only": 1}), "No tuition posts match")

    def test_all_tabs_and_load_more(self):
        for _ in range(6):
            self.publish()
        self.client.force_login(self.tutor)
        url = reverse("tuition:find_tuition")
        self.assertContains(self.client.get(url), "Load More")
        self.assertNotContains(self.client.get(url, {"limit": 8}), "Load More")
        for tab in ("posts", "recommended", "applications", "saved"):
            self.assertEqual(self.client.get(url, {"tab": tab}).status_code, 200)

    def test_student_cannot_open_find_tuition(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse("tuition:find_tuition"))
        self.assertRedirects(r, reverse("role_dashboard"), fetch_redirect_response=False)

    def test_save_toggle(self):
        self.publish()
        post = TuitionPost.objects.get()
        self.client.force_login(self.tutor)
        url = reverse("tuition:toggle_save", args=[post.pk])
        self.client.post(url)
        self.assertEqual(SavedPost.objects.count(), 1)
        self.assertContains(self.client.get(reverse("tuition:find_tuition"), {"tab": "saved"}), "Mathematics")
        self.client.post(url)
        self.assertEqual(SavedPost.objects.count(), 0)

    # ---- screen 11 ------------------------------------------------------
    def test_detail_apply_and_duplicate(self):
        self.publish()
        post = TuitionPost.objects.get()
        self.client.force_login(self.tutor)
        r = self.client.get(post.get_absolute_url())
        self.assertContains(r, "Apply Now")
        self.assertContains(r, "Exact address hidden")
        self.client.post(reverse("tuition:apply", args=[post.pk]), {"message": "Hello"})
        self.client.post(reverse("tuition:apply", args=[post.pk]), {"message": "Again"})
        self.assertEqual(Application.objects.count(), 1)
        self.assertContains(self.client.get(post.get_absolute_url()), "You applied")

    def test_student_sees_no_apply_panel(self):
        self.publish()
        post = TuitionPost.objects.get()
        self.assertNotContains(self.client.get(post.get_absolute_url()), "Apply Now")

    def test_unverified_tutor_cannot_apply(self):
        self.publish()
        post = TuitionPost.objects.get()
        unverified = make_user("newtutor", "TUTOR", verified=False)
        self.client.force_login(unverified)
        self.assertContains(self.client.get(post.get_absolute_url()), "Verification needed")
        self.client.post(reverse("tuition:apply", args=[post.pk]), {"message": "x"})
        self.assertEqual(Application.objects.count(), 0)

    def test_superuser_counts_as_admin(self):
        self.publish()
        post = TuitionPost.objects.get()
        boss = User.objects.create_superuser("boss", "b@x.com", "pw12345!")
        self.client.force_login(boss)
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

    def test_paused_post_rejects_application(self):
        self.publish()
        post = TuitionPost.objects.get()
        post.status = "PAUSED"
        post.save()
        self.client.force_login(self.tutor)
        self.client.post(reverse("tuition:apply", args=[post.pk]), {"message": "x"})
        self.assertEqual(Application.objects.count(), 0)

    def test_comment_reply_edit_delete(self):
        self.publish()
        post = TuitionPost.objects.get()
        self.client.force_login(self.tutor)
        self.client.post(reverse("tuition:add_comment", args=[post.pk]), {"body": "Is Higher Math needed?"})
        top = Comment.objects.get()
        self.client.force_login(self.student)
        self.client.post(reverse("tuition:add_comment", args=[post.pk]), {"body": "Only General Math.", "parent": top.pk})
        reply = Comment.objects.get(parent=top)
        # reply to a reply stays one level deep
        self.client.post(reverse("tuition:add_comment", args=[post.pk]), {"body": "Thanks!", "parent": reply.pk})
        self.assertEqual(Comment.objects.filter(parent=top).count(), 2)
        r = self.client.get(post.get_absolute_url())
        self.assertContains(r, "Post owner")
        self.assertContains(r, "Discussion · 3 comments")

        # only the author can edit; others get 404
        self.client.post(reverse("tuition:edit_comment", args=[top.pk]), {"body": "hacked"})
        top.refresh_from_db()
        self.assertEqual(top.body, "Is Higher Math needed?")
        self.client.force_login(self.tutor)
        self.client.post(reverse("tuition:edit_comment", args=[top.pk]), {"body": "Edited"})
        top.refresh_from_db()
        self.assertTrue(top.edited)

        # a stranger can't delete someone else's comment
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(reverse("tuition:delete_comment", args=[top.pk])).status_code, 403)
        self.client.force_login(self.tutor)
        self.client.post(reverse("tuition:delete_comment", args=[top.pk]))
        self.assertEqual(Comment.objects.count(), 0)  # replies cascade

    def test_draft_is_private(self):
        self.client.force_login(self.student)
        self.client.post(reverse("tuition:create_post"), {**POST_DATA, "save_draft": "1"})
        post = TuitionPost.objects.get()
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)
        self.client.force_login(self.tutor)
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get(reverse("tuition:find_tuition")).status_code, 302)

    # ---- my posts + matching -------------------------------------------
    def test_my_posts_status_changes(self):
        self.publish()
        post = TuitionPost.objects.get()
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("tuition:my_posts")), "Mathematics")
        self.client.post(reverse("tuition:change_status", args=[post.pk]), {"action": "pause"})
        post.refresh_from_db()
        self.assertEqual(post.status, "PAUSED")
        self.client.force_login(self.tutor)
        r = self.client.post(reverse("tuition:change_status", args=[post.pk]), {"action": "close"})
        self.assertRedirects(r, reverse("role_dashboard"), fetch_redirect_response=False)
        post.refresh_from_db()
        self.assertEqual(post.status, "PAUSED")

    def test_match_score_is_bounded_and_neutral_without_profile(self):
        self.publish()
        post = TuitionPost.objects.get()
        result = calculate_match(self.tutor, post)
        self.assertTrue(0 <= result.total <= 100)
        self.assertEqual(set(result.breakdown), {"subject", "budget", "location", "availability", "mode", "trust"})
