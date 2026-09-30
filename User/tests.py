from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import Client, RequestFactory, SimpleTestCase

from .views import (
	PregnancyProfile,
	PregnancyTracker,
	WeeklyRecordHistory,
	AIPredictionValues,
	ai_pregnancy_screening,
	assess_pregnancy_screening,
	pregnancy_is_complete,
	pregnancy_week_for,
)


class PregnancyTrackerWeekPreviewTests(SimpleTestCase):
	def render_tracker(self, requested_week, elapsed_days=28):
		lmp_date = date.today() - timedelta(days=elapsed_days)
		current_week = pregnancy_week_for(lmp_date)
		pregnancy = SimpleNamespace(
			last_period_date=lmp_date,
			current_week=current_week,
			current_month=max(1, min(10, (current_week - 1) // 4 + 1)),
			weekly_records=MagicMock(),
		)
		self.weekly_record_manager = pregnancy.weekly_records

		user = SimpleNamespace(pregnancy_records=MagicMock())
		user.pregnancy_records.first.return_value = pregnancy

		milestones = MagicMock()
		milestones.first.return_value = None
		milestones.__bool__.return_value = False
		milestones.__iter__.return_value = iter([])

		request = RequestFactory().get(
			'/User/PregnancyTracker/',
			{'week': requested_week},
		)
		with patch('User.views.guard', return_value=(user, None)), \
				patch('User.views.tbl_Milestone.objects.filter', return_value=milestones), \
				patch('User.views.nutrition_recommendations', return_value=[]) as recommendations:
			response = PregnancyTracker(request)

		return response, recommendations

	def render_history(self, requested_week=None, saved_records=None):
		pregnancy = SimpleNamespace(
			last_period_date=date.today() - timedelta(days=28),
			weekly_records=MagicMock(),
		)
		user = SimpleNamespace(pregnancy_records=MagicMock())
		user.pregnancy_records.first.return_value = pregnancy
		weekly_records = MagicMock()
		weekly_records.select_related.return_value.order_by.return_value = saved_records or []
		query = {'week': requested_week} if requested_week is not None else {}
		request = RequestFactory().get('/User/WeeklyRecordHistory/', query)
		with patch('User.views.guard', return_value=(user, None)), \
				patch('User.views.tbl_PregnancyWeeklyRecord.objects.filter', return_value=weekly_records), \
				patch('User.views.nutrition_recommendations', return_value=[]) as recommendations:
			response = WeeklyRecordHistory(request)
		return response, recommendations

	def test_tracker_always_shows_current_week_recommendations(self):
		response, recommendations = self.render_tracker(12)

		recommendations.assert_called_once_with(pregnancy_week=5, limit=8)
		self.assertContainsText(response, 'Week 5 Nutrition Recommendations')
		self.assertContainsText(response, '/User/WeeklyRecordHistory/')
		self.assertContainsText(response, '5/41 weeks')

	def test_completed_week_one_is_saved_when_week_two_starts(self):
		self.render_tracker(2, elapsed_days=7)

		self.weekly_record_manager.get_or_create.assert_called_once_with(week=1)

	def test_week_above_40_falls_back_to_current_week(self):
		response, recommendations = self.render_tracker(41)

		recommendations.assert_called_once_with(pregnancy_week=5, limit=8)
		self.assertContainsText(response, 'Weekly Milestone (Week 5)')

	def test_history_shows_recommendations_for_selected_week(self):
		response, recommendations = self.render_history(2)

		recommendations.assert_called_once_with(pregnancy_week=2, limit=8)
		self.assertContainsText(response, 'Week 2 Nutrition Recommendations')

	def test_history_hides_recommendations_until_a_week_is_selected(self):
		response, recommendations = self.render_history()

		recommendations.assert_not_called()
		self.assertNotIn('Nutrition Recommendations', response.content.decode())

	def test_tracker_links_to_separate_weekly_record_history(self):
		response, _ = self.render_tracker(5)

		self.assertContainsText(response, 'View Weekly Record History')
		self.assertNotIn('value="4"', response.content.decode())

	def test_weekly_record_history_lists_saved_weeks_and_recommendation_links(self):
		saved_records = [
			SimpleNamespace(week=4, recorded_at=date.today(), notes='Week four notes'),
			SimpleNamespace(week=3, recorded_at=date.today(), notes='Week three notes'),
		]
		response, _ = self.render_history(saved_records=saved_records)

		self.assertContainsText(response, 'Week four notes')
		self.assertContainsText(response, 'Week three notes')
		self.assertContainsText(response, '?week=4')

	def test_week_41_is_the_final_tracker_week(self):
		response, recommendations = self.render_tracker(41, elapsed_days=280)

		recommendations.assert_not_called()
		self.assertContainsText(response, '41/41 weeks')
		self.assertContainsText(response, 'Week 41 is in progress')

	def test_week_41_completion_boundary(self):
		self.assertEqual(pregnancy_week_for(date.today() - timedelta(days=280)), 41)
		self.assertEqual(pregnancy_week_for(date.today() - timedelta(days=400)), 41)
		self.assertFalse(pregnancy_is_complete(date.today() - timedelta(days=286)))
		self.assertTrue(pregnancy_is_complete(date.today() - timedelta(days=287)))

	def test_saved_lmp_is_not_editable_before_week_41_completes(self):
		lmp_date = date.today() - timedelta(days=28)
		pregnancy = SimpleNamespace(
			last_period_date=lmp_date,
			expected_delivery_date=lmp_date + timedelta(days=280),
			current_week=5,
			current_month=2,
			save=MagicMock(),
		)
		user = SimpleNamespace(pregnancy_records=MagicMock())
		user.pregnancy_records.first.return_value = pregnancy
		request = RequestFactory().get('/User/PregnancyProfile/')

		with patch('User.views.guard', return_value=(user, None)):
			response = PregnancyProfile(request)

		self.assertNotIn('name="last_period_date"', response.content.decode())
		self.assertContainsText(response, 'cannot be edited during this pregnancy')

	def test_profile_only_offers_new_lmp_after_week_41_completes(self):
		for elapsed_days, form_visible in ((28, False), (287, True)):
			lmp_date = date.today() - timedelta(days=elapsed_days)
			current_week = pregnancy_week_for(lmp_date)
			pregnancy = SimpleNamespace(
				last_period_date=lmp_date,
				expected_delivery_date=lmp_date + timedelta(days=280),
				current_week=current_week,
				current_month=max(1, min(10, (current_week - 1) // 4 + 1)),
				save=MagicMock(),
			)
			user = SimpleNamespace(pregnancy_records=MagicMock())
			user.pregnancy_records.first.return_value = pregnancy
			request = RequestFactory().get('/User/PregnancyProfile/')

			with patch('User.views.guard', return_value=(user, None)):
				response = PregnancyProfile(request)

			self.assertEqual('name="last_period_date"' in response.content.decode(), form_visible)
			if form_visible:
				self.assertContainsText(response, 'Start New Pregnancy')

	def test_new_pregnancy_creates_a_record_after_week_41(self):
		old_lmp = date.today() - timedelta(days=287)
		new_lmp = date.today() - timedelta(days=14)
		pregnancy = SimpleNamespace(
			last_period_date=old_lmp,
			weekly_records=MagicMock(),
		)
		user = SimpleNamespace(pregnancy_records=MagicMock())
		user.pregnancy_records.first.return_value = pregnancy
		request = RequestFactory().post(
			'/User/PregnancyProfile/',
			{'last_period_date': new_lmp.isoformat()},
		)

		with patch('User.views.guard', return_value=(user, None)), \
				patch('User.views.tbl_PregnancyTracker.objects.create') as create_record, \
				patch('User.views.messages.success'):
			response = PregnancyProfile(request)

		create_record.assert_called_once_with(
			user=user,
			last_period_date=new_lmp,
			expected_delivery_date=new_lmp + timedelta(days=280),
			current_week=3,
		)
		self.assertEqual(response.status_code, 302)

	def test_active_pregnancy_rejects_lmp_edits(self):
		pregnancy = SimpleNamespace(last_period_date=date.today() - timedelta(days=28))
		user = SimpleNamespace(pregnancy_records=MagicMock())
		user.pregnancy_records.first.return_value = pregnancy
		request = RequestFactory().post(
			'/User/PregnancyProfile/',
			{'last_period_date': date.today().isoformat()},
		)

		with patch('User.views.guard', return_value=(user, None)), \
				patch('User.views.messages.error') as error_message, \
				patch('User.views.tbl_PregnancyTracker.objects.create') as create_record:
			response = PregnancyProfile(request)

		error_message.assert_called_once()
		create_record.assert_not_called()
		self.assertEqual(response.status_code, 302)

	def assertContainsText(self, response, text):
		self.assertIn(text.encode(), response.content)


class PregnancyScreeningTests(SimpleTestCase):
	def test_period_delay_recommends_a_test_without_diagnosing_pregnancy(self):
		result = assess_pregnancy_screening(28, 8, [])

		self.assertEqual(result['label'], 'Pregnancy test recommended')
		self.assertIn('cannot confirm pregnancy', result['guidance'])

	def test_urgent_symptom_recommends_immediate_care(self):
		result = assess_pregnancy_screening(28, 0, ['heavy_bleeding'])

		self.assertEqual(result['level'], 'urgent')
		self.assertIn('now', result['guidance'])

	def test_prediction_form_uses_screening_inputs_not_vital_sign_model(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.predict_maternal_risk') as vital_sign_model, \
				patch('User.views.get_gemini_api_key', return_value='test-key'), \
				patch(
					'User.views.call_gemini_api',
					return_value=({'reply': 'Mocked AI screening guidance.', 'model': 'test-model'}, None),
				) as gemini_model:
			response = client.post(
				'/User/AIPrediction/',
				{
					'age': '28',
					'period_delay_days': '8',
					'symptoms': ['nausea'],
				},
			)

		self.assertContains(response, 'Next step:')
		self.assertContains(response, 'Consult a doctor for advice.')
		self.assertContains(response, 'Mocked AI screening guidance.')
		self.assertNotContains(response, 'Could pregnancy be possible?')
		self.assertNotContains(response, 'Adult screening inputs')
		self.assertContains(response, 'Pregnancy is possible, but age, symptoms, and a delayed period cannot confirm it.')
		self.assertContains(response, 'Gemini AI (test-model)')
		gemini_model.assert_called_once()
		prompt = gemini_model.call_args.args[0][0]['text']
		self.assertIn('age=28 years; period delay=8 days', prompt)
		self.assertIn('selected symptoms=Nausea', prompt)
		vital_sign_model.assert_not_called()

	def test_period_delay_sets_qualitative_status(self):
		with patch('User.views.get_gemini_api_key', return_value=''):
			late = ai_pregnancy_screening(28, 8, ['nausea'])
			not_late = ai_pregnancy_screening(28, 0, ['nausea'])

		self.assertIn('pregnancy is possible', late['pregnancy_status'].lower())
		self.assertIn('cannot determine pregnancy', not_late['pregnancy_status'])

	def test_minor_inputs_are_not_sent_to_gemini(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.get_gemini_api_key') as get_api_key, \
				patch('User.views.call_gemini_api') as gemini_model:
			for age, expected_text in (
				('4', 'Immediate pediatric assessment needed'),
				('17', 'Adult screening unavailable for minors'),
			):
				response = client.post(
					'/User/AIPrediction/',
					{
						'age': age,
						'period_delay_days': '8',
						'symptoms': ['none'],
					},
				)
				self.assertContains(response, expected_text)

		get_api_key.assert_not_called()
		gemini_model.assert_not_called()

	def test_symptom_choice_is_required_and_no_symptoms_is_valid(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.get_gemini_api_key', return_value='test-key'), \
				patch(
					'User.views.call_gemini_api',
					return_value=({'reply': 'Mocked screening guidance.', 'model': 'test-model'}, None),
				) as gemini_model:
			missing_symptom = client.post(
				'/User/AIPrediction/',
				{'age': '28', 'period_delay_days': '8'},
			)
			no_symptoms = client.post(
				'/User/AIPrediction/',
				{'age': '28', 'period_delay_days': '8', 'symptoms': ['none']},
			)

		self.assertContains(missing_symptom, 'Select at least one symptom or choose No symptoms.')
		self.assertContains(no_symptoms, 'Mocked screening guidance.')
		gemini_model.assert_called_once()

	def test_invalid_or_missing_required_fields_show_inline_errors(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.get_gemini_api_key') as get_api_key, \
				patch('User.views.call_gemini_api') as gemini_model:
			response = client.post(
				'/User/AIPrediction/',
				{
					'age': '28.5',
					'period_delay_days': '400',
					'symptoms': ['unknown_symptom'],
				},
			)

		self.assertContains(response, 'Age must be a whole number.')
		self.assertContains(response, 'Period delay must be between 0 and 365 days.')
		self.assertContains(response, 'Choose symptoms from the list')
		self.assertContains(response, 'value="28.5"')
		get_api_key.assert_not_called()
		gemini_model.assert_not_called()

	def test_ai_result_cannot_override_urgent_symptom_guidance(self):
		with patch('User.views.get_gemini_api_key', return_value='test-key'), \
				patch(
					'User.views.call_gemini_api',
					return_value=({'reply': 'Everything is fine.', 'model': 'test-model'}, None),
				):
			result = ai_pregnancy_screening(28, 0, ['heavy_bleeding'])

		self.assertEqual(result['level'], 'urgent')
		self.assertIn('urgent assessment', result['guidance'])

	def test_missing_ai_key_uses_labeled_non_ai_fallback(self):
		with patch('User.views.get_gemini_api_key', return_value=''), \
				patch('User.views.call_gemini_api') as gemini_model:
			result = ai_pregnancy_screening(28, 8, [])

		self.assertIn('fallback', result['source'])
		gemini_model.assert_not_called()


class ValuesBasedPredictionTests(SimpleTestCase):
	def test_valid_values_go_directly_to_trained_model(self):
		client = Client()
		model_result = {'label': 'Mid Risk', 'confidence': 82.5, 'error': None}
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.predict_maternal_risk', return_value=model_result) as model, \
				patch('User.views.is_data_in_dataset') as dataset_check:
			response = client.post(
				'/User/AIPredictionValues/',
				{
					'age': '28',
					'systolic': '127',
					'diastolic': '83',
					'blood_sugar': '7.35',
					'body_temperature': '98.6',
					'heart_rate': '78',
				},
			)

		model.assert_called_once_with(
			age=28,
			systolicbp=127,
			diastolicbp=83,
			blood_sugar=7.35,
			bodytemp=98.6,
			heartrate=78,
		)
		dataset_check.assert_not_called()
		self.assertContains(response, 'Mid Risk')
		self.assertContains(response, 'Values-Based Maternal Risk Prediction')

	def test_out_of_range_values_do_not_reach_model(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch('User.views.predict_maternal_risk') as model:
			response = client.post(
				'/User/AIPredictionValues/',
				{
					'age': '28',
					'systolic': '20',
					'diastolic': '83',
					'blood_sugar': '7',
					'body_temperature': '98.6',
					'heart_rate': '78',
				},
			)

		model.assert_not_called()
		self.assertContains(response, 'Systolic blood pressure must be between 60 and 220.')

	def test_high_risk_result_prompts_doctor_consultation(self):
		client = Client()
		with patch('User.views.guard', return_value=(SimpleNamespace(), None)), \
				patch(
					'User.views.predict_maternal_risk',
					return_value={'label': 'High Risk', 'confidence': 91.0, 'error': None},
				):
			response = client.post(
				'/User/AIPredictionValues/',
				{
					'age': '25',
					'systolic': '130',
					'diastolic': '80',
					'blood_sugar': '15',
					'body_temperature': '98',
					'heart_rate': '86',
				},
			)

		self.assertContains(response, 'Please consult a doctor promptly')
		self.assertContains(response, 'This model prediction is not a diagnosis.')
