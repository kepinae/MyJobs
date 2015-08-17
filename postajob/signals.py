from django.db.models import Count
from django.db.models.signals import post_save

from postajob.models import Job, JobLocation

def remove_orphaned_job_locations(sender, **kwargs):
    # If there are no Jobs related to a JobLocation, it shouldn't exist in Solr
    #
    # change_m2m signals detecting job locations being removed
    # were complicated and unreliable. We're trying to enforce a foriegn key
    # with cascade delete from JobLocation to Job in the index, but not the
    # database
    from import_jobs import delete_by_guid
    orphaned_job_locations = JobLocation.objects.annotate(
                                job_count=Count('jobs')
                                ).filter(job_count=0)
    delete_by_guid([location.guid for location in orphaned_job_locations])

post_save.connect(remove_orphaned_job_locations, Job)
