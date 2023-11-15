import os
from django.conf import settings
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS


# browser
# city
# country
# continent
# date
# defaultChannelGroup
# deviceCategory
# FirstUserCampaignName
# FirstUserGoogleAdsAdNetworkType
# firstUserSource
# fullPageUrl
# averageSessionDuration
# engagedSessions

class GoogleAnalytics:
    property_id = settings.PROPERTY_ID

    @classmethod
    def get_property(cls):
        return f"properties/{cls.property_id}"

    @classmethod
    def get_date_obj(cls, start_date, end_date):
        if start_date and end_date:
            date_obj = DateRange(start_date=start_date, end_date=end_date)
        elif start_date:
            date_obj = DateRange(start_date=start_date, end_date="today")
        elif end_date:
            date_obj = DateRange(start_date="2020-01-01", end_date=end_date)
        else:
            date_obj = DateRange(start_date="2020-01-01", end_date="today")
        return date_obj

    @classmethod
    def visitors_report(cls, start_date=None, end_date=None):
        client = BetaAnalyticsDataClient()
        ga_property = cls.get_property()
        date_obj = cls.get_date_obj(start_date, end_date)

        request = RunReportRequest(
            property=ga_property,
            metrics=[Metric(name="activeUsers"), Metric(name="sessions"), Metric(name="averageSessionDuration")],
            date_ranges=[date_obj]
        )

        response = client.run_report(request)
        active_users = response.rows[0].metric_values[0].value
        website_visits = response.rows[0].metric_values[1].value
        avg_engagement_time = response.rows[0].metric_values[2].value
        return active_users, website_visits, int(float(avg_engagement_time))

    @classmethod
    def cities_report(cls, start_date=None, end_date=None):
        city_report = []
        client = BetaAnalyticsDataClient()
        ga_property = cls.get_property()

        date_obj = cls.get_date_obj(start_date, end_date)

        request = RunReportRequest(
            property=ga_property,
            dimensions=[Dimension(name="country"), Dimension(name="city")],
            metrics=[Metric(name="activeUsers")],
            date_ranges=[date_obj]
        )
        response = client.run_report(request)

        for row in response.rows:
            obj = {
                'country': row.dimension_values[0].value,
                'city': row.dimension_values[1].value,
                'visitors': row.metric_values[0].value
            }
            city_report.append(obj)

        return city_report
