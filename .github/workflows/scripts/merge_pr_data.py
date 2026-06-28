#!/usr/bin/env python3
"""Merge reviews.json + review_comments.json into pr_data.json for chatlog.py."""
import json, sys

pr_data = json.load(open("/tmp/pr_data.json"))
pr_data["reviews"] = json.load(open("/tmp/reviews.json"))
pr_data["review_comments"] = json.load(open("/tmp/review_comments.json"))
json.dump(pr_data, open("/tmp/pr_data.json", "w"), ensure_ascii=False)
