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
        try:
            active_users = response.rows[0].metric_values[0].value
        except IndexError:
            active_users = 0
        try:
            website_visits = response.rows[0].metric_values[1].value
        except IndexError:
            website_visits = 0
        try:
            avg_engagement_time = response.rows[0].metric_values[2].value
        except IndexError:
            avg_engagement_time = 0
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

    @classmethod
    def pages_report(cls, start_date=None, end_date=None):
        page_report = []
        client = BetaAnalyticsDataClient()

        request = RunReportRequest(property=cls.get_property(),
                                   date_ranges=[cls.get_date_obj(start_date, end_date)],
                                   dimensions=[Dimension(name="pagePath")],
                                   metrics=[Metric(name="screenPageViews"), Metric(name="averageSessionDuration")])
        response = client.run_report(request=request)
        for row in response.rows:
            obj = {
                'page_path': row.dimension_values[0].value,
                'visitors': row.metric_values[0].value,
                'avg_engagement_time': int(float(row.metric_values[1].value))
            }
            page_report.append(obj)

        return page_report

    @classmethod
    def device_report(cls, start_date=None, end_date=None):
        device_report = []
        client = BetaAnalyticsDataClient()

        request = RunReportRequest(
            property=cls.get_property(),
            date_ranges=[cls.get_date_obj(start_date, end_date)],
            dimensions=[Dimension(name="deviceCategory"), Dimension(name="mobileDeviceModel")],
            metrics=[Metric(name="activeUsers")]
        )
        response = client.run_report(request=request)

        for row in response.rows:
            obj = {
                'category': row.dimension_values[0].value,
                'model': row.dimension_values[1].value,
                'visitors': row.metric_values[0].value
            }
            device_report.append(obj)
        return device_report

    @classmethod
    def channels_report(cls, start_date=None, end_date=None):
        channel_report = []
        client = BetaAnalyticsDataClient()

        request = RunReportRequest(
            property=cls.get_property(),
            date_ranges=[cls.get_date_obj(start_date, end_date)],
            dimensions=[Dimension(name="sessionDefaultChannelGrouping")],
            metrics=[Metric(name="sessions")]
        )

        response = client.run_report(request=request)

        for row in response.rows:
            obj = {
                'channel': row.dimension_values[0].value,
                'visitors': row.metric_values[0].value,
            }
            channel_report.append(obj)
        return channel_report
